import os
import uuid
import torch
import logging
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Log environment variables for debugging
logger = logging.getLogger(__name__)
logger.info(f"Environment variables:")
logger.info(f"CHUNK_SIZE={os.environ.get('CHUNK_SIZE')}")
logger.info(f"CHUNK_OVERLAP={os.environ.get('CHUNK_OVERLAP')}")
logger.info(f"CHUNK_STRATEGY={os.environ.get('CHUNK_STRATEGY')}")

from dataclasses import dataclass
from typing import List, Dict
from langchain.schema import Document
from pathlib import Path

from qdrant_client import QdrantClient
from langchain_qdrant import QdrantVectorStore
from langchain_huggingface import HuggingFaceEmbeddings
from qdrant_client.http.models import Distance, VectorParams, Filter, FieldCondition, MatchValue
from chunking import ChunkingStrategy, H2ChunkingStrategy, CharacterChunkingStrategy

from langchain_community.document_loaders import (
    TextLoader,
    CSVLoader,
    Docx2txtLoader,
    UnstructuredExcelLoader,
    PyMuPDFLoader,
    UnstructuredPowerPointLoader,
    ObsidianLoader,
)

from storage import MinimaStore, IndexingStatus

logger = logging.getLogger(__name__)


class Config:
    def __init__(self):
        self.EXTENSIONS_TO_LOADERS = {
            ".pdf": PyMuPDFLoader,
            ".pptx": UnstructuredPowerPointLoader,
            ".ppt": UnstructuredPowerPointLoader,
            ".xls": UnstructuredExcelLoader,
            ".xlsx": UnstructuredExcelLoader,
            ".docx": Docx2txtLoader,
            ".doc": Docx2txtLoader,
            ".txt": TextLoader,
            ".md": ObsidianLoader,
            ".csv": CSVLoader,
        }
        
        self.DEVICE = torch.device(
            "mps" if torch.backends.mps.is_available() else
            "cuda" if torch.cuda.is_available() else
            "cpu"
        )
        
        self.START_INDEXING = os.environ.get("START_INDEXING")
        self.LOCAL_FILES_PATH = os.environ.get("LOCAL_FILES_PATH")
        self.CONTAINER_PATH = os.environ.get("CONTAINER_PATH")
        self.QDRANT_COLLECTION = "mnm_storage"
        self.QDRANT_BOOTSTRAP = "qdrant"
        self.EMBEDDING_MODEL_ID = os.environ.get("EMBEDDING_MODEL_ID")
        self.EMBEDDING_SIZE = os.environ.get("EMBEDDING_SIZE")
        
        # Initialize chunking configuration
        self.CHUNK_SIZE = int(os.environ.get('CHUNK_SIZE', 500))
        self.CHUNK_OVERLAP = int(os.environ.get('CHUNK_OVERLAP', 200))
        self.CHUNK_STRATEGY = os.environ.get('CHUNK_STRATEGY', 'character').lower()
        
        # Log the configuration values
        logger.info(f"Loaded CHUNK_SIZE={self.CHUNK_SIZE} from environment (default=500)")
        logger.info(f"Loaded CHUNK_OVERLAP={self.CHUNK_OVERLAP} from environment (default=200)")
        logger.info(f"Loaded CHUNK_STRATEGY={self.CHUNK_STRATEGY} from environment (default=character)")
        logger.info(f"Raw env values: CHUNK_SIZE={os.environ.get('CHUNK_SIZE')}, "
                  f"CHUNK_OVERLAP={os.environ.get('CHUNK_OVERLAP')}, "
                  f"CHUNK_STRATEGY={os.environ.get('CHUNK_STRATEGY')}")

class Indexer:
    def __init__(self):
        self.config = Config()
        self.qdrant = self._initialize_qdrant()
        self.embed_model = self._initialize_embeddings()
        self.document_store = self._setup_collection()
        self.text_splitter = self._initialize_text_splitter()

    def _initialize_qdrant(self) -> QdrantClient:
        return QdrantClient(host=self.config.QDRANT_BOOTSTRAP)

    def _initialize_embeddings(self) -> HuggingFaceEmbeddings:
        return HuggingFaceEmbeddings(
            model_name=self.config.EMBEDDING_MODEL_ID,
            model_kwargs={'device': self.config.DEVICE},
            encode_kwargs={'normalize_embeddings': False}
        )

    def _initialize_text_splitter(self) -> ChunkingStrategy:
        logger.info(f"Initializing text splitter with strategy: {self.config.CHUNK_STRATEGY}")
        
        if self.config.CHUNK_STRATEGY == 'h2':
            logger.info("Using H2 chunking strategy")
            return H2ChunkingStrategy(
                chunk_size=self.config.CHUNK_SIZE,
                chunk_overlap=self.config.CHUNK_OVERLAP
            )
        
        logger.info("Using Character chunking strategy")
        return CharacterChunkingStrategy(
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
        self.qdrant.create_payload_index(
            collection_name=self.config.QDRANT_COLLECTION,
            field_name="fpath",
            field_schema="keyword"
        )
        return QdrantVectorStore(
            client=self.qdrant,
            collection_name=self.config.QDRANT_COLLECTION,
            embedding=self.embed_model,
        )

    def _create_loader(self, file_path: str):
        file_extension = Path(file_path).suffix.lower()
        loader_class = self.config.EXTENSIONS_TO_LOADERS.get(file_extension)
        
        if not loader_class:
            raise ValueError(f"Unsupported file type: {file_extension}")
        
        if loader_class == ObsidianLoader:
            # Use the container path for ObsidianLoader
            return loader_class(path=self.config.CONTAINER_PATH, collect_metadata=True)
        
        return loader_class(file_path=file_path)

    def _process_file(self, loader, file_path: str) -> List[str]:
        try:
            # Special handling for ObsidianLoader
            if isinstance(loader, ObsidianLoader):
                logger.info(f"Processing with ObsidianLoader: {file_path}")
                # Load all documents from the directory
                all_docs = loader.load()
                logger.info(f"Loaded {len(all_docs)} total documents")
                
                # Get relative path from container path for matching
                rel_path = os.path.relpath(file_path, self.config.CONTAINER_PATH)
                logger.info(f"Looking for relative path: {rel_path}")
                
                # Log all document sources for debugging
                sources = [doc.metadata.get('source', '') for doc in all_docs]
                logger.info(f"Available document sources: {sources}")
                
                # Filter for our specific file using relative path
                documents = []
                for doc in all_docs:
                    source = doc.metadata.get('source', '')
                    if source:
                        # Convert source to absolute path if it's relative
                        if not os.path.isabs(source):
                            source = os.path.join(self.config.CONTAINER_PATH, source)
                        
                        # Normalize both paths for comparison
                        source_path = os.path.normpath(source)
                        target_path = os.path.normpath(file_path)
                        
                        logger.info(f"Comparing source '{source_path}' with target '{target_path}'")
                        
                        # Try both exact match and relative path match
                        if source_path == target_path or source_path.endswith(rel_path):
                            logger.info(f"Found matching document with source: {source}")
                            documents.append(doc)
                
                logger.info(f"Found {len(documents)} matching documents")
                
                # Apply text splitting if we found our document
                if documents:
                    # Convert documents to chunks using our new chunking strategy
                    chunked_docs = []
                    for doc in documents:
                        chunks = self.text_splitter.split_text(doc.page_content, doc.metadata)
                        for chunk in chunks:
                            # Create new document for each chunk
                            chunked_docs.append(Document(
                                page_content=chunk.text,
                                metadata={**doc.metadata, **{
                                    'chunk_start': chunk.start_char,
                                    'chunk_end': chunk.end_char
                                }}
                            ))
                    documents = chunked_docs
                    logger.info(f"Split into {len(documents)} chunks")
            else:
                raw_docs = loader.load()
                chunked_docs = []
                for doc in raw_docs:
                    chunks = self.text_splitter.split_text(doc.page_content, doc.metadata)
                    for chunk in chunks:
                        chunked_docs.append(Document(
                            page_content=chunk.text,
                            metadata={**doc.metadata, **{
                                'chunk_start': chunk.start_char,
                                'chunk_end': chunk.end_char
                            }}
                        ))
                documents = chunked_docs
            if not documents:
                logger.warning(f"No documents loaded from {file_path}")
                return []

            logger.info("Processing documents for Qdrant insertion")
            for doc in documents:
                # Add file path to metadata
                doc.metadata['file_path'] = file_path
                # Remove redundant path field if it exists
                if 'path' in doc.metadata:
                    del doc.metadata['path']
                
                # Extract and consolidate all tags
                if isinstance(loader, ObsidianLoader):
                    all_tags = set()
                    
                # Process frontmatter tags
                if 'tags' in doc.metadata:
                    frontmatter_tags = doc.metadata['tags']
                    # Handle string format (both comma-separated and YAML array string)
                    if isinstance(frontmatter_tags, str):
                        # First try to handle as comma-separated list
                        if ',' in frontmatter_tags:
                            all_tags.update(tag.strip() for tag in frontmatter_tags.split(','))
                        # Then try ObsidianLoader's TAG_REGEX for #tag format
                        matches = ObsidianLoader.TAG_REGEX.finditer(frontmatter_tags)
                        all_tags.update(match.group(1) for match in matches if match)
                        # Finally try to evaluate as YAML array string
                        if frontmatter_tags.startswith('[') and frontmatter_tags.endswith(']'):
                            try:
                                import ast
                                yaml_tags = ast.literal_eval(frontmatter_tags)
                                if isinstance(yaml_tags, list):
                                    all_tags.update(yaml_tags)
                            except:
                                pass
                    # Handle list format
                    elif isinstance(frontmatter_tags, list):
                        all_tags.update(frontmatter_tags)
                    
                    # Process inline tags from content
                    content_matches = ObsidianLoader.TAG_REGEX.finditer(doc.page_content)
                    all_tags.update(match.group(1) for match in content_matches if match)
                    
                    # Filter out 'None' values and empty strings
                    all_tags = {tag for tag in all_tags if tag and tag != 'None'}
                    
                    # Store as a sorted list
                    if all_tags:
                        doc.metadata['tags'] = sorted(list(all_tags))
                    else:
                        doc.metadata['tags'] = []
                    
                    # Remove redundant tag fields
                    for field in ['global_tags', 'inline_tags']:
                        if field in doc.metadata:
                            del doc.metadata[field]

            uuids = [str(uuid.uuid4()) for _ in range(len(documents))]
            logger.info(f"Generated {len(uuids)} UUIDs for document insertion")
            
            try:
                logger.info("Starting document embedding process")
                # Log a sample document to verify content
                if documents:
                    sample = documents[0]
                    logger.info(f"Sample document content: {sample.page_content[:200]}")
                    logger.info(f"Sample document metadata: {sample.metadata}")

                logger.info("Attempting to add documents to Qdrant")
                ids = self.document_store.add_documents(documents=documents, ids=uuids)
                logger.info(f"Successfully added {len(ids)} documents to Qdrant from {file_path}")
                
                # Log document details for verification
                for i, doc in enumerate(documents):
                    logger.info(f"Document {i} metadata: {doc.metadata}")
                    logger.info(f"Document {i} content preview: {doc.page_content[:100]}...")
                
                return ids
            except Exception as e:
                logger.error(f"Failed to add documents to Qdrant: {str(e)}")
                return []
            
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {str(e)}")
            return []

    def index(self, message: Dict[str, any]) -> None:
        start = time.time()
        path, file_id, last_updated_seconds = message["path"], message["file_id"], message["last_updated_seconds"]
        logger.info(f"Processing file: {path} (ID: {file_id})")
        indexing_status: IndexingStatus = MinimaStore.check_needs_indexing(fpath=path, last_updated_seconds=last_updated_seconds)
        if indexing_status != IndexingStatus.no_need_reindexing:
            logger.info(f"Indexing needed for {path} with status: {indexing_status}")
            try:
                if indexing_status == IndexingStatus.need_reindexing:
                    logger.info(f"Removing {path} from index storage for reindexing")
                    self.remove_from_storage(files_to_remove=[path])
                loader = self._create_loader(path)
                ids = self._process_file(loader, path)
                if ids:
                    logger.info(f"Successfully indexed {path} with IDs: {ids}")
            except Exception as e:
                logger.error(f"Failed to index file {path}: {str(e)}")
        else:
            logger.info(f"Skipping {path}, no indexing required. timestamp didn't change")
        end = time.time()
        logger.info(f"Processing took {end - start} seconds for file {path}")

    def purge(self, message: Dict[str, any]) -> None:
        existing_file_paths: list[str] = message["existing_file_paths"]
        files_to_remove = MinimaStore.find_removed_files(existing_file_paths=set(existing_file_paths))
        if len(files_to_remove) > 0:
            logger.info(f"purge processing removing old files {files_to_remove}")
            self.remove_from_storage(files_to_remove)
        else:
            logger.info("Nothing to purge")

    def remove_from_storage(self, files_to_remove: list[str]):
        filter_conditions = Filter(
            must=[
                FieldCondition(
                    key="fpath",
                    match=MatchValue(value=fpath)
                )
                for fpath in files_to_remove
            ]
        )
        response = self.qdrant.delete(
            collection_name=self.config.QDRANT_COLLECTION,
            points_selector=filter_conditions,
            wait=True
        )
        logger.info(f"Delete response for {len(files_to_remove)} for files: {files_to_remove} is: {response}")

    def find(self, query: str) -> Dict[str, any]:
        try:
            logger.info(f"Searching for: {query}")
            found = self.document_store.search(query, search_type="similarity")
            
            if not found:
                logger.info("No results found")
                return {"links": set(), "output": ""}

            links = set()
            results = []
            
            for item in found:
                path = item.metadata["file_path"].replace(
                    self.config.CONTAINER_PATH,
                    self.config.LOCAL_FILES_PATH
                )
                links.add(f"file://{path}")
                results.append(item.page_content)

            output = {
                "links": links,
                "output": ". ".join(results)
            }
            
            logger.info(f"Found {len(found)} results")
            return output
            
        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            return {"error": "Unable to find anything for the given query"}

    def embed(self, query: str):
        return self.embed_model.embed_query(query)
