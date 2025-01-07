import os
import uuid
import torch
import logging
import fnmatch
from dataclasses import dataclass
from datetime import datetime
from typing import List, Set, Dict, Optional
from pathlib import Path

from qdrant_client import QdrantClient
from langchain_qdrant import QdrantVectorStore
from langchain_huggingface import HuggingFaceEmbeddings
from qdrant_client.http.models import Distance, VectorParams
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    TextLoader,
    CSVLoader,
    Docx2txtLoader,
    UnstructuredExcelLoader,
    PyMuPDFLoader,
    ObsidianLoader,
)

from cleanup import QdrantCleanup  # Changed from relative to absolute import

logger = logging.getLogger(__name__)

@dataclass
class Config:
    EXTENSIONS_TO_LOADERS = {
        ".pdf": PyMuPDFLoader,
        ".xls": UnstructuredExcelLoader,
        ".docx": Docx2txtLoader,
        ".txt": TextLoader,
        ".md": ObsidianLoader,
        ".csv": CSVLoader,
    }
    
    DEVICE = torch.device(
        "mps" if torch.backends.mps.is_available() else
        "cuda" if torch.cuda.is_available() else
        "cpu"
    )
    
    START_INDEXING = os.environ.get("START_INDEXING")
    LOCAL_FILES_PATH = os.environ.get("LOCAL_FILES_PATH")
    CONTAINER_PATH = os.environ.get("CONTAINER_PATH")
    QDRANT_COLLECTION = "mnm_storage"
    QDRANT_BOOTSTRAP = "qdrant"
    EMBEDDING_MODEL_ID = os.environ.get("EMBEDDING_MODEL_ID")
    EMBEDDING_SIZE = os.environ.get("EMBEDDING_SIZE")
    RERANKER_MODEL = os.environ.get("RERANKER_MODEL")
    
    CHUNK_SIZE = int(os.environ.get("CHUNK_SIZE"))
    CHUNK_OVERLAP = int(os.environ.get("CHUNK_OVERLAP"))

class Indexer:
    def __init__(self):
        self.config = Config()
        self.qdrant = self._initialize_qdrant()
        self.embed_model = self._initialize_embeddings()
        self.document_store = self._setup_collection()
        self.text_splitter = self._initialize_text_splitter()
        self.ignore_patterns = self._load_ignore_patterns()
        
    def cleanup_duplicates(self) -> Dict[str, int]:
        """Clean up duplicate embeddings from the collection."""
        cleanup = QdrantCleanup(self.qdrant, self.config.QDRANT_COLLECTION)
        return cleanup.cleanup_duplicates()

    def _load_ignore_patterns(self) -> List[str]:
        """Load patterns from .minimaignore file if it exists"""
        ignore_file = os.path.join(self.config.CONTAINER_PATH, '.minimaignore')
        patterns = []
        if os.path.exists(ignore_file):
            try:
                with open(ignore_file, 'r') as f:
                    patterns = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                logger.info(f"Loaded {len(patterns)} ignore patterns from .minimaignore")
            except Exception as e:
                logger.error(f"Error loading .minimaignore: {e}")
        return patterns

    def _should_ignore(self, path: str) -> bool:
        """Check if a file should be ignored based on .minimaignore patterns"""
        try:
            relative_path = os.path.relpath(path, self.config.CONTAINER_PATH)
            logger.debug(f"Checking if {relative_path} should be ignored")
            for pattern in self.ignore_patterns:
                if fnmatch.fnmatch(relative_path, pattern):
                    logger.debug(f"File {relative_path} matches ignore pattern {pattern}")
                    return True
            return False
        except ValueError as e:
            logger.error(f"Error checking ignore pattern for {path}: {e}")
            return False

    def _initialize_qdrant(self) -> QdrantClient:
        return QdrantClient(host=self.config.QDRANT_BOOTSTRAP)

    def _initialize_embeddings(self) -> HuggingFaceEmbeddings:
        return HuggingFaceEmbeddings(
            model_name=self.config.EMBEDDING_MODEL_ID,
            model_kwargs={'device': self.config.DEVICE},
            encode_kwargs={'normalize_embeddings': False}
        )

    def _initialize_text_splitter(self) -> RecursiveCharacterTextSplitter:
        if os.environ.get("CHUNK_STRATEGY") == "h2":
            from langchain.text_splitter import MarkdownHeaderTextSplitter
            headers_to_split_on = [
                ("#", "Header 1"),
                ("##", "Header 2"),
            ]
            return MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
        else:
            return RecursiveCharacterTextSplitter(
                chunk_size=self.config.CHUNK_SIZE,
                chunk_overlap=self.config.CHUNK_OVERLAP
            )

    def _setup_collection(self) -> QdrantVectorStore:
        if not self.qdrant.collection_exists(self.config.QDRANT_COLLECTION):
            self.qdrant.create_collection(
                collection_name=self.config.QDRANT_COLLECTION,
                vectors_config=VectorParams(
                    size=self.config.EMBEDDING_SIZE,
                    distance=Distance.COSINE
                ),
            )
        return QdrantVectorStore(
            client=self.qdrant,
            collection_name=self.config.QDRANT_COLLECTION,
            embedding=self.embed_model,
        )

    def _create_loader(self, file_path: str):
        if self._should_ignore(file_path):
            raise ValueError(f"File ignored by .minimaignore: {file_path}")
            
        file_extension = Path(file_path).suffix.lower()
        loader_class = self.config.EXTENSIONS_TO_LOADERS.get(file_extension)
        
        if not loader_class:
            raise ValueError(f"Unsupported file type: {file_extension}")
        
        # Special handling for ObsidianLoader
        if loader_class == ObsidianLoader:
            directory = str(Path(file_path).parent)
            return ObsidianLoader(
                directory,
                encoding="utf-8",
                collect_metadata=True
            )
        
        return loader_class(file_path=file_path)

    def _process_file(self, loader) -> List[str]:
        """Process a file and add it to the document store"""
        try:
            # Load documents
            documents = loader.load()
                
            if not documents:
                logger.warning(f"No documents loaded from {loader.file_path}")
                return []
            if os.environ.get("CHUNK_STRATEGY") == "h2":
                new_documents = []
                for doc in documents:
                    split_docs = self.text_splitter.split_text(doc.page_content)
                    for split_doc in split_docs:
                        new_doc = type(doc)(page_content=split_doc, metadata=doc.metadata)
                        new_documents.append(new_doc)
                documents = new_documents
            else:
                # Split documents if any were loaded
                if documents:
                    documents = self.text_splitter.split_documents(documents)

            # Process each document
            for doc in documents:
                # Standardize file path
                logger.info(f"Document metadata before path standardization: {doc.metadata}")
                doc.metadata['file_path'] = doc.metadata.get('path') or doc.metadata.get('source')
                logger.info(f"Document metadata after path standardization: {doc.metadata}")

                # For Obsidian files, standardize metadata
                if isinstance(loader, ObsidianLoader):
                    # Handle tags
                    tags = set()
                    if 'tags' in doc.metadata:
                        if isinstance(doc.metadata['tags'], str):
                            tags.update(tag.strip() for tag in doc.metadata['tags'].split(','))
                        elif isinstance(doc.metadata['tags'], (list, set)):
                            tags.update(doc.metadata['tags'])

                    # Standardize dates
                    for date_field, alt_field in [('created', 'created_at'), ('last_modified', 'modified_at')]:
                        if date_field in doc.metadata:
                            try:
                                value = doc.metadata[date_field]
                                if isinstance(value, (int, float)):
                                    # Handle Unix timestamp
                                    iso_date = datetime.fromtimestamp(value).isoformat()
                                elif isinstance(value, str):
                                    # Try parsing ISO format or common date formats
                                    try:
                                        dt = datetime.fromisoformat(value.replace(" ", "T"))
                                    except ValueError:
                                        import dateutil.parser
                                        dt = dateutil.parser.parse(value)
                                    iso_date = dt.isoformat()
                                else:
                                    continue
                                doc.metadata[alt_field] = iso_date
                            except Exception as e:
                                logger.debug(f"Could not parse {date_field} value '{value}': {e}")

                    # Standardize metadata
                    logger.info(f"Original metadata before update: {doc.metadata}")
                    doc.metadata.update({
                        "tags": list(tags),
                        "created_at": doc.metadata.get('created_at'),
                        "modified_at": doc.metadata.get('modified_at')
                    })

                    # Clean up redundant fields
                    for field in ['path', 'frontmatter', 'source']:
                        doc.metadata.pop(field, None)

            # Generate IDs and add to store
            uuids = [str(uuid.uuid4()) for _ in range(len(documents))]
            ids = self.document_store.add_documents(documents=documents, ids=uuids)
            
            logger.info(f"Successfully processed {len(ids)} documents from {loader.file_path}")
            return ids
            
        except Exception as e:
            logger.error(f"Error processing file {loader.file_path}: {str(e)}")
            return []

    def index(self, message: Dict[str, str]) -> None:
        path, file_id = message["path"], message["file_id"]
        logger.info(f"Processing file: {path} (ID: {file_id})")
        
        try:
            loader = self._create_loader(path)
            ids = self._process_file(loader)
            if ids:
                logger.info(f"Successfully indexed {path} with IDs: {ids}")
        except ValueError as e:
            if "ignored by .minimaignore" in str(e):
                logger.info(str(e))  # Log ignored files as info, not error
            else:
                logger.error(f"Failed to index file {path}: {str(e)}")
        except Exception as e:
            logger.error(f"Failed to index file {path}: {str(e)}")

    def find(self, query: str) -> Dict[str, any]:
        try:
            logger.info(f"Searching for: {query}")
            query_vector = self.embed_model.embed_query(query)
            
            # Get initial results
            search_result = self.qdrant.search(
                collection_name=self.config.QDRANT_COLLECTION,
                query_vector=query_vector,
                limit=20,
                with_payload=True,
                search_params={
                    "exact": False,
                    "hnsw_ef": 128
                }
            )
            
            if not search_result:
                logger.info("No results found")
                return {"links": set(), "results": []}

            # Use a dictionary to track unique results by file path
            unique_results = {}
            
            for hit in search_result:
                try:
                    # Get file path from either metadata or root
                    metadata = hit.payload.get('metadata', {})
                    path = (metadata.get('file_path') or 
                        hit.payload.get('file_path') or 
                        metadata.get('source') or 
                        hit.payload.get('source'))
                    
                    if not path:
                        logger.warning(f"No path found in payload: {hit.payload}")
                        continue
                    
                    # Normalize path
                    path = path.replace(self.config.CONTAINER_PATH, self.config.LOCAL_FILES_PATH)
                    path = path.replace('\\', '/')
                    
                    # Only process if we haven't seen this file yet or if the score is better
                    if path not in unique_results or hit.score > unique_results[path]["metadata"]["scores"]["similarity"]:
                        file_url = f"file://{path}"
                        
                        # Calculate relevance score
                        relevance_score = hit.score * 100
                        
                        # Apply boosts
                        if "modified_at" in metadata:
                            try:
                                modified_days = (datetime.now() - datetime.fromisoformat(metadata["modified_at"])).days
                                recency_boost = max(0, (30 - modified_days) / 30) * 20
                                relevance_score += recency_boost
                            except Exception as e:
                                logger.debug(f"Error calculating date boost: {e}")
                        
                        tags = metadata.get("tags", [])
                        if tags and len(tags) > 0:
                            tag_boost = len(tags) * 5
                            relevance_score += min(tag_boost, 20)
                        
                        result = {
                            "content": hit.payload.get("page_content", ""),
                            "metadata": {
                                "file": {
                                    "url": file_url,
                                    "filename": os.path.basename(path)
                                },
                                "tags": tags,
                                "links": metadata.get("links", []),
                                "created_at": metadata.get('created_at'),
                                "modified_at": metadata.get('modified_at'),
                                "scores": {
                                    "relevance": round(relevance_score, 2),
                                    "similarity": round(hit.score * 100, 2)
                                }
                            }
                        }
                        unique_results[path] = result
                        
                except Exception as e:
                    logger.error(f"Error processing search result: {e}")
                    continue
            
            if not unique_results:
                logger.warning("No valid results found after processing")
                return {"links": [], "results": []}
            
            # Convert to list and sort by relevance
            results = list(unique_results.values())
            results.sort(key=lambda x: x["metadata"]["scores"]["relevance"], reverse=True)
            
            # Take top 10 results
            results = results[:10]
            
            # Get unique links
            links = [result["metadata"]["file"]["url"] for result in results]
            
            # Wrap the results in a 'content' array as per MCP format
            content = [
                {
                    "type": "text",
                    "text": f"Found {len(results)} results from {len(set(links))} unique files",
                },
                {
                    "type": "application/json",
                    "json": {
                        "links": links,
                        "results": results,
                        "metadata": {
                            "total_results": len(results),
                            "unique_files": len(set(links))
                        }
                    }
                }
            ]
            
            logger.info(content[0]["text"])
            return {"content": content}
                
        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            return {"error": "Unable to find anything for the given query"}
