import os
import uuid
import torch
import logging
import fnmatch
from dataclasses import dataclass
from typing import List, Set, Dict, Optional
from pathlib import Path

from qdrant_client import QdrantClient
from langchain_qdrant import QdrantVectorStore
from langchain_huggingface import HuggingFaceEmbeddings
from qdrant_client.http.models import Distance, VectorParams
from langchain.text_splitter import RecursiveCharacterTextSplitter

from transformers import AutoModelForSequenceClassification, AutoTokenizer
from langchain_community.document_loaders import (
    TextLoader,
    CSVLoader,
    Docx2txtLoader,
    UnstructuredExcelLoader,
    PyMuPDFLoader,
)


logger = logging.getLogger(__name__)


@dataclass
class Config:
    EXTENSIONS_TO_LOADERS = {
        ".pdf": PyMuPDFLoader,
        ".xls": UnstructuredExcelLoader,
        ".docx": Docx2txtLoader,
        ".txt": TextLoader,
        ".md": TextLoader,
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
    
    CHUNK_SIZE = 500
    CHUNK_OVERLAP = 200

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
        # Look for .minimaignore in the container path since that's where the mounted files are
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
        # Get path relative to container mount point for consistent pattern matching
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
        
        return loader_class(file_path=file_path)

    def _process_file(self, loader) -> List[str]:
        try:
            documents = loader.load_and_split(self.text_splitter)
            if not documents:
                logger.warning(f"No documents loaded from {loader.file_path}")
                return []

            for doc in documents:
                doc.metadata['file_path'] = loader.file_path

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
            found = self.document_store.search(query, search_type="similarity")
            
            if not found:
                logger.info("No results found")
                return {"links": set(), "output": ""}

            links = set()
            results = []
            
            # Rerank results if reranker is configured
            if self.reranker:
                tokenizer, model = self.reranker
                # Prepare pairs of (query, document) for reranking
                pairs = [(query, doc.page_content) for doc in found]
                inputs = tokenizer(pairs, padding=True, truncation=True, return_tensors="pt")
                with torch.no_grad():
                    scores = model(**inputs).logits
                # Sort documents by reranker scores
                sorted_docs = [doc for _, doc in sorted(zip(scores, found), reverse=True)]
            else:
                sorted_docs = found

            for item in sorted_docs:
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
