import os
import uuid
import torch
import logging
import fnmatch
import hashlib
import re
from dataclasses import dataclass
from datetime import datetime
from typing import List, Set, Dict, Optional
from pathlib import Path

from qdrant_client import QdrantClient
from langchain_qdrant import QdrantVectorStore
from langchain_huggingface import HuggingFaceEmbeddings
from qdrant_client.http.models import Distance, VectorParams
from langchain.text_splitter import RecursiveCharacterTextSplitter

from transformers import AutoModelForSequenceClassification, AutoTokenizer
from datetime import datetime
from langchain_community.document_loaders import (
    TextLoader,
    CSVLoader,
    Docx2txtLoader,
    UnstructuredExcelLoader,
    PyMuPDFLoader,
    ObsidianLoader,
)


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
        self.reranker = self._initialize_reranker()
        
    def _initialize_reranker(self):
        if not self.config.RERANKER_MODEL:
            return None
            
        logger.info(f"Initializing reranker model: {self.config.RERANKER_MODEL}")
        tokenizer = AutoTokenizer.from_pretrained(self.config.RERANKER_MODEL)
        model = AutoModelForSequenceClassification.from_pretrained(self.config.RERANKER_MODEL)
        return (tokenizer, model)

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

    def _process_tags(self, metadata: Dict) -> Set[str]:
        """Process and clean tags from document metadata
        Handles both frontmatter tags and inline tags while removing duplicates and invalid tags.
        
        Args:
            metadata: Document metadata dictionary containing tags
            
        Returns:
            Set of cleaned and validated tags
        """
        tags = set()
        
        # Process frontmatter tags
        if 'tags' in metadata:
            raw_tags = metadata['tags']
            logger.debug(f"Processing frontmatter tags: {raw_tags}")
            
            if isinstance(raw_tags, str):
                # Handle comma-separated string tags
                tags.update(tag.strip() for tag in raw_tags.split(','))
            elif isinstance(raw_tags, (list, set)):
                # Handle list/set of tags
                tags.update(str(tag).strip() for tag in raw_tags if tag)
                
        # Process inline tags if they exist
        if 'inline_tags' in metadata:
            inline_tags = metadata['inline_tags']
            logger.debug(f"Processing inline tags: {inline_tags}")
            tags.update(inline_tags)
            
        # Clean and validate tags
        clean_tags = set()
        for tag in tags:
            # Skip empty tags
            if not tag or not tag.strip():
                continue
                
            # Clean the tag
            tag = tag.strip('#').strip()
            
            # Skip invalid tags
            if not self._validate_tag(tag):
                logger.debug(f"Skipping invalid tag: {tag}")
                continue
                
            # Skip path-based tags
            if self._is_path_based_tag(tag, metadata.get('file_path', '')):
                logger.debug(f"Skipping path-based tag: {tag}")
                continue
                
            clean_tags.add(tag)
            
        logger.info(f"Processed tags: {clean_tags}")
        return clean_tags
        
    def _validate_tag(self, tag: str) -> bool:
        """Validate if a tag is legitimate."""
        invalid_patterns = ['.md', '.txt', '\\', ' ']  # Allow forward slashes for hierarchy
        return not any(pattern in tag for pattern in invalid_patterns)
        
    def _is_path_based_tag(self, tag: str, filepath: str) -> bool:
        """Check if tag is derived from file path or name."""
        if not filepath:
            return False
            
        # Normalize paths and tags for comparison
        filepath_parts = [p.lower() for p in Path(filepath).parts]
        filename = Path(filepath).stem.lower()
        tag_lower = tag.lower()
        
        return (
            tag_lower in filepath_parts or  # Check if tag matches any path component
            tag_lower == filename or  # Check if tag matches filename without extension
            any(tag_lower == part.lower() for part in filepath.split('/'))
        )

    def _process_file(self, loader) -> List[str]:
        """Process a file and add it to the document store"""
        try:
            # Load documents based on loader type
            if isinstance(loader, ObsidianLoader):
                documents = loader.load()
            else:
                documents = loader.load()
                
            # Split documents if any were loaded
            if documents:
                documents = self.text_splitter.split_documents(documents)
            
            if not documents:
                logger.warning(f"No documents loaded from {loader.file_path}")
                return []

            # Process each document
            for doc in documents:
                # Standardize file path
                doc.metadata['file_path'] = doc.metadata['path']

                # For Obsidian files, standardize metadata
                if isinstance(loader, ObsidianLoader):
                    # First, make sure we have the full file path
                    doc.metadata['file_path'] = os.path.abspath(doc.metadata['path'])
                    
                    # Extract and save inline tags before processing
                    inline_tags = {match.group(1) for match in re.finditer(r'#([^\s#]+(?:/[^\s#]+)*)', doc.page_content)}
                    doc.metadata['inline_tags'] = inline_tags
                    
                    # Process all tags using the new method
                    tags = self._process_tags(doc.metadata)


                    # Standardize dates
                    for date_field, alt_field in [('created', 'created_at'), ('last_modified', 'modified_at')]:
                        if date_field in doc.metadata:
                            try:
                                value = doc.metadata[date_field]
                                if isinstance(value, (int, float)):
                                    # Handle Unix timestamp
                                    timestamp = float(value)
                                    iso_date = datetime.fromtimestamp(timestamp).isoformat()
                                elif isinstance(value, str):
                                    # Try parsing ISO format or common date formats
                                    try:
                                        dt = datetime.fromisoformat(value.replace(" ", "T"))
                                    except ValueError:
                                        import dateutil.parser
                                        dt = dateutil.parser.parse(value)
                                        timestamp = dt.timestamp()
                                    iso_date = dt.isoformat()
                                else:
                                    continue
                                # Store both timestamp and ISO date
                                doc.metadata[alt_field] = iso_date
                                doc.metadata[f"{alt_field}_timestamp"] = timestamp
                            except Exception as e:
                                logger.debug(f"Could not parse {date_field} value '{value}': {e}")

                    # Standardize metadata
                    doc.metadata.update({
                        "tags": list(tags),
                        "created_at": doc.metadata.get('created_at'),
                        "created_at_timestamp": doc.metadata.get('created_at_timestamp'),
                        "modified_at": doc.metadata.get('modified_at'),
                        "modified_at_timestamp": doc.metadata.get('modified_at_timestamp')
                    })

                    # Clean up redundant fields
                    for field in ['path', 'frontmatter', 'source']:
                        doc.metadata.pop(field, None)

            # Generate content-based UUIDs and add to store
            uuids = [self._generate_content_uuid(doc) for doc in documents]
            logger.info(f"Generated UUIDs: {uuids}")
            
            ids = self.document_store.add_documents(documents=documents, ids=uuids)
            
            logger.info(f"Successfully processed {len(ids)} documents from {loader.file_path} with UUIDs: {ids}")
            
            # Log first few characters of content with their UUIDs for verification
            for doc, uid in zip(documents, uuids):
                preview = doc.page_content[:50] + '...' if len(doc.page_content) > 50 else doc.page_content
                logger.info(f"Content preview: {preview} -> UUID: {uid}")
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

    def cleanup_tags(self) -> Dict[str, any]:
        """Clean up tags in all documents in the index.
        - Removes duplicate tags
        - Removes path-based tags
        - Validates all tags
        - Updates documents with cleaned tags
        """
        try:
            # Get all documents
            results = self.qdrant.scroll(
                collection_name=self.config.QDRANT_COLLECTION,
                limit=1000  # Adjust if you have more documents
            )
            
            if not results or not results[0]:
                return {"message": "No documents found", "processed": 0, "updated": 0}
                
            processed = 0
            updated = 0
            
            for point in results[0]:
                processed += 1
                
                # Skip if no metadata or tags
                if not point.payload or 'metadata' not in point.payload:
                    continue
                    
                metadata = point.payload['metadata']
                if 'tags' not in metadata:
                    continue
                    
                # Process tags using our new method
                old_tags = set(metadata['tags'])
                clean_tags = self._process_tags(metadata)
                
                # Update document if tags changed
                if old_tags != clean_tags:
                    logger.info(f"Updating tags for document {point.id}")
                    logger.info(f"Old tags: {old_tags}")
                    logger.info(f"New tags: {clean_tags}")
                    
                    # Update the document's tags
                    metadata['tags'] = list(clean_tags)
                    self.qdrant.set_payload(
                        collection_name=self.config.QDRANT_COLLECTION,
                        payload={'metadata': metadata},
                        points=[point.id]
                    )
                    updated += 1
            
            return {
                "message": "Successfully cleaned up tags",
                "processed": processed,
                "updated": updated,
                "details": f"Processed {processed} documents, updated {updated} with cleaned tags"
            }
            
        except Exception as e:
            logger.error(f"Tag cleanup failed: {str(e)}")
            return {"error": f"Unable to clean up tags: {str(e)}"}

    def find(self, query: str) -> Dict[str, any]:
        try:
            logger.info(f"Searching for: {query}")
            # First do semantic search with higher limit
            found = self.document_store.search(
                query,
                search_type="similarity_score_threshold",
                score_threshold=0.5,  # Adjust this threshold as needed
                k=100  # Get more results initially for better filtering
            )
            
            # Log the exact structure from Qdrant
            if found:
                logger.info("Structure of first found document:")
                logger.info(f"Document keys: {found[0].__dict__.keys()}")
                logger.info(f"Metadata: {found[0].metadata}")
                logger.info(f"Tags in metadata: {found[0].metadata.get('tags', [])}")
                if 'tags' in found[0].metadata:
                    logger.info(f"Tag type in metadata: {type(found[0].metadata['tags'])}")

            if not found:
                logger.info("No results found")
                return {"links": set(), "output": ""}

            links = set()
            results = []
            
            # Rerank results if reranker is configured
            if self.reranker:
                tokenizer, model = self.reranker
                # Prepare pairs of (query, document) for reranking with proper separator
                pairs = [(f"{query} [SEP] {doc.page_content}") for doc in found]
                inputs = tokenizer(
                    pairs,
                    padding=True,
                    truncation=True,
                    return_tensors="pt",
                    max_length=512,
                    add_special_tokens=True
                )
                with torch.no_grad():
                    scores = model(**inputs).logits
                # Sort documents by reranker scores
                sorted_docs = [doc for _, doc in sorted(zip(scores, found), reverse=True)]
            else:
                sorted_docs = found

            seen_contents = set()
            unique_results = []
            
            for item in sorted_docs:
                path = item.metadata["file_path"].replace(
                    self.config.CONTAINER_PATH,
                    self.config.LOCAL_FILES_PATH
                )
                links.add(f"file://{path}")
                
                # Skip duplicate content
                if item.page_content in seen_contents:
                    continue
                seen_contents.add(item.page_content)
                
                # Calculate relevance score based on metadata
                relevance_score = 1.0
                metadata = item.metadata
                
                # Increase score for recent documents
                if "modified_at" in metadata:
                    try:
                        modified_days = (datetime.now() - datetime.fromisoformat(metadata["modified_at"])).days
                        relevance_score += max(0, (30 - modified_days) / 30)  # Recent documents get higher score
                    except:
                        pass
                
                # Increase score for documents with tags
                if "tags" in metadata and len(metadata["tags"]) > 0:
                    relevance_score += 0.5
                
                # Extract and include metadata if available
                result = {
                    "content": item.page_content,
                    "metadata": {
                        "file_path": path,  # Include the file path
                        "tags": metadata.get("tags", []),
                        "links": metadata.get("links", []),
                        "created_at": metadata.get("created_at"),
                        "modified_at": metadata.get("modified_at"),
                        "relevance_score": relevance_score
                    }
                }
                unique_results.append(result)

            # Sort results by relevance score
            unique_results.sort(key=lambda x: x["metadata"]["relevance_score"], reverse=True)

            output = {
                "links": links,
                "output": unique_results,  # Pass the full results array
                "metadata": [r["metadata"] for r in unique_results],
                "relevance_scores": [r["metadata"]["relevance_score"] for r in unique_results]
            }
            
            logger.info(f"Found {len(found)} results")
            return output
            
        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            return {"error": "Unable to find anything for the given query"}

    def embed(self, query: str):
        return self.embed_model.embed_query(query)
        
    def cleanup_ignored_files(self) -> Dict[str, any]:
        """Remove documents from ignored directories from the index"""
        try:
            from qdrant_client.http.models import Filter, FieldCondition, MatchAny, MatchText
            
            # Log all documents first to see what paths we have
            all_results = self.qdrant.scroll(
                collection_name=self.config.QDRANT_COLLECTION,
                limit=1000
            )
            
            if all_results and all_results[0]:
                logger.info("Found documents with paths:")
                for point in all_results[0]:
                    if 'metadata' in point.payload and 'file_path' in point.payload['metadata']:
                        logger.info(f"File path: {point.payload['metadata']['file_path']}")
            
            # Patterns to match in file paths - include variations
            ignored_patterns = [
                '.trash', 'trash/', '.trash/', 
                '.obsidian', '.obsidian/', 
                '.smart-env', '.smart-env/',
                '/.trash/', '/trash/',
                '/.obsidian/', 
                '/.smart-env/'
            ]
            
            # Find documents matching these patterns using text matching
            conditions = [
                FieldCondition(
                    key="metadata.file_path",
                    match=MatchText(text=pattern)
                )
                for pattern in ignored_patterns
            ]
            
            # Create a filter that matches any of these patterns
            cleanup_filter = Filter(should=conditions)
            
            # Get matching points to count them and log them
            results = self.qdrant.scroll(
                collection_name=self.config.QDRANT_COLLECTION,
                scroll_filter=cleanup_filter,
                limit=1000  # Adjust if you have more documents
            )
            
            # Log matched documents
            if results and results[0]:
                logger.info("Found documents matching ignore patterns:")
                for point in results[0]:
                    if 'metadata' in point.payload and 'file_path' in point.payload['metadata']:
                        logger.info(f"Matched file path: {point.payload['metadata']['file_path']}")

            
            if not results or not results[0]:
                return {"message": "No documents found matching cleanup criteria", "deleted_count": 0}
            
            # Get the IDs of documents to delete
            points_to_delete = [point.id for point in results[0]]
            
            # Delete the documents
            self.qdrant.delete(
                collection_name=self.config.QDRANT_COLLECTION,
                points_selector=points_to_delete
            )
            
            return {
                "message": "Successfully cleaned up ignored files",
                "deleted_count": len(points_to_delete),
                "deleted_ids": points_to_delete
            }
            
        except Exception as e:
            logger.error(f"Cleanup failed: {str(e)}")
            return {"error": f"Unable to clean up ignored files: {str(e)}"}
        
    def find_by_date_range(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> Dict[str, any]:
        """Retrieve documents within a specified date range, sorted by date"""
        try:
            # Build filter conditions using Qdrant's filter syntax
            from qdrant_client.http.models import Filter, FieldCondition, Range
            
            conditions = []
            if start_date:
                # Convert datetime to Unix timestamp
                start_ts = start_date.timestamp()
                logger.info(f"Start date {start_date.isoformat()} converted to timestamp: {start_ts}")
                conditions.append(
                    FieldCondition(
                        key="metadata.modified_at_timestamp",
                        range=Range(gte=start_ts)
                    )
                )
            if end_date:
                # Convert datetime to Unix timestamp
                end_ts = end_date.timestamp()
                logger.info(f"End date {end_date.isoformat()} converted to timestamp: {end_ts}")
                conditions.append(
                    FieldCondition(
                        key="metadata.modified_at_timestamp",
                        range=Range(lte=end_ts)
                    )
                )
                
            filter_conditions = Filter(must=conditions) if conditions else None
            
            # Log the filter conditions
            logger.info(f"Using filter conditions: {filter_conditions}")

            # Query Qdrant using the filter
            results = self.qdrant.scroll(
                collection_name=self.config.QDRANT_COLLECTION,
                scroll_filter=filter_conditions,
                limit=100  # Adjust limit as needed
            )

            if not results or not results[0]:
                logger.info("No results found matching the date range")
                return {"links": set(), "output": []}

            # Process results
            links = set()
            processed_results = []
            seen_contents = set()

            for point in results[0]:
                try:
                    # Skip if we've seen this content before
                    if point.payload["page_content"] in seen_contents:
                        continue
                    seen_contents.add(point.payload["page_content"])

                    # Process file path
                    path = point.payload["metadata"]["file_path"].replace(
                        self.config.CONTAINER_PATH,
                        self.config.LOCAL_FILES_PATH
                    )
                    links.add(f"file://{path}")

                    # Create result entry
                    result = {
                        "content": point.payload["page_content"],
                        "metadata": {
                            "file_path": path,
                            "tags": point.payload["metadata"].get("tags", []),
                            "created_at": point.payload["metadata"].get("created_at"),
                            "modified_at": point.payload["metadata"].get("modified_at"),
                            "relevance_score": 1.0  # Base score for date-based results
                        }
                    }
                    processed_results.append(result)
                except Exception as e:
                    logger.error(f"Error processing result: {str(e)}")
                    continue

            # Sort by modified_at date
            processed_results.sort(
                key=lambda x: x["metadata"]["modified_at"] or "",
                reverse=True
            )
            
            logger.info(f"Found {len(processed_results)} documents in date range")

            return {
                "links": links,
                "output": processed_results,
                "metadata": [r["metadata"] for r in processed_results],
                "relevance_scores": [r["metadata"]["relevance_score"] for r in processed_results]
            }

        except Exception as e:
            logger.error(f"Date range search failed: {str(e)}")
            return {"error": "Unable to search by date range"}
        
    def verify_document_uuid(self, document) -> Dict[str, any]:
        """Check if a document with the same content-based UUID exists"""
        generated_uuid = self._generate_content_uuid(document)
        
        # Search in Qdrant for this UUID
        points = self.qdrant.retrieve(
            collection_name=self.config.QDRANT_COLLECTION,
            ids=[generated_uuid]
        )
        
        exists = len(points) > 0
        return {
            "uuid": generated_uuid,
            "exists": exists,
            "content_preview": document.page_content[:50] + '...' if exists else None
        }
        
    def _generate_content_uuid(self, document) -> str:
        """Generate a deterministic UUID based on document content and metadata"""
        # Combine relevant fields for hashing
        content = document.page_content
        file_path = document.metadata.get('file_path', '')
        modified_at = document.metadata.get('modified_at', '')
        
        # Add other relevant metadata if available
        tags = ','.join(sorted(document.metadata.get('tags', []))) if 'tags' in document.metadata else ''
        
        # Create a deterministic hash string
        hash_input = f"{content}{file_path}{modified_at}{tags}".encode('utf-8')
        content_hash = hashlib.sha256(hash_input).hexdigest()
        
        # Convert hash to UUID format using namespace
        # Using NAMESPACE_OID as it's appropriate for document identifiers
        return str(uuid.uuid5(uuid.NAMESPACE_OID, content_hash))
