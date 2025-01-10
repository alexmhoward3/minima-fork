import os
import uuid
import hashlib
import fnmatch
import logging
from typing import List, Optional, Type
from datetime import datetime
from pathlib import Path

import torch
from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter, TextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from .config import ProcessingConfig
from .models import ProcessedDocument

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """Handles document processing, including loading, chunking, and embedding generation"""
    
    def __init__(self, config: ProcessingConfig):
        self.config = config
        self.text_splitter = self._initialize_text_splitter()
        self.embed_model = self._initialize_embeddings()
        self.reranker = self._initialize_reranker()
        self.ignore_patterns = self._load_ignore_patterns()
        
    def _initialize_text_splitter(self) -> TextSplitter:
        """Initializes the text splitter based on the configuration."""
        if self.config.processing.chunk_strategy == "h1":
            return MarkdownHeaderTextSplitter(
                headers_to_split_on=[("#", "Header 1")],
            )
        
        return RecursiveCharacterTextSplitter(
            chunk_size=self.config.processing.chunk_size,
            chunk_overlap=self.config.processing.chunk_overlap,
            length_function=len,
            is_separator_regex=False,
        )
        
    def _initialize_embeddings(self) -> HuggingFaceEmbeddings:
        return HuggingFaceEmbeddings(
            model_name=self.config.EMBEDDING_MODEL_ID,
            model_kwargs={'device': self.config.DEVICE},
            encode_kwargs={'normalize_embeddings': False}
        )
        
    def _initialize_reranker(self):
        if not self.config.RERANKER_MODEL:
            return None
            
        logger.info(f"Initializing reranker model: {self.config.RERANKER_MODEL}")
        tokenizer = AutoTokenizer.from_pretrained(self.config.RERANKER_MODEL)
        model = AutoModelForSequenceClassification.from_pretrained(self.config.RERANKER_MODEL)
        model.to(self.config.DEVICE)
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
            for pattern in self.ignore_patterns:
                if fnmatch.fnmatch(relative_path, pattern):
                    logger.debug(f"File {relative_path} matches ignore pattern {pattern}")
                    return True
            return False
        except ValueError as e:
            logger.error(f"Error checking ignore pattern for {path}: {e}")
            return False
            
    def _create_loader(self, file_path: str):
        """Create appropriate document loader based on file extension"""
        if self._should_ignore(file_path):
            raise ValueError(f"File ignored by .minimaignore: {file_path}")
            
        file_extension = Path(file_path).suffix.lower()
        loader_class = self.config.EXTENSIONS_TO_LOADERS.get(file_extension)
        
        if not loader_class:
            raise ValueError(f"Unsupported file type: {file_extension}")
        
        # Special handling for ObsidianLoader
        if loader_class.__name__ == 'ObsidianLoader':
            directory = str(Path(file_path).parent)
            return loader_class(
                directory,
                encoding="utf-8",
                collect_metadata=True
            )
        
        return loader_class(file_path=file_path)
        
    def _generate_uuid(self, content: str, metadata: dict) -> str:
        """Generate a deterministic UUID based on document content and metadata"""
        file_path = metadata.get('file_path', '')
        modified_at = metadata.get('modified_at', '')
        tags = ','.join(sorted(metadata.get('tags', [])))
        
        hash_input = f"{content}{file_path}{modified_at}{tags}".encode('utf-8')
        content_hash = hashlib.sha256(hash_input).hexdigest()
        
        return str(uuid.uuid5(uuid.NAMESPACE_OID, content_hash))
        
    def _standardize_metadata(self, metadata: dict) -> dict:
        """Standardize metadata fields"""
        standardized = metadata.copy()
        
        # Handle tags
        tags = set()
        if 'tags' in metadata:
            if isinstance(metadata['tags'], str):
                tags.update(tag.strip() for tag in metadata['tags'].split(','))
            elif isinstance(metadata['tags'], (list, set)):
                tags.update(metadata['tags'])
        standardized['tags'] = list(tags)
        
        # Standardize dates
        for date_field, alt_field in [('created', 'created_at'), ('last_modified', 'modified_at')]:
            if date_field in metadata:
                try:
                    value = metadata[date_field]
                    if isinstance(value, (int, float)):
                        iso_date = datetime.fromtimestamp(value).isoformat()
                    elif isinstance(value, str):
                        try:
                            dt = datetime.fromisoformat(value.replace(" ", "T"))
                        except ValueError:
                            from dateutil import parser
                            dt = parser.parse(value)
                        iso_date = dt.isoformat()
                    else:
                        continue
                    standardized[alt_field] = iso_date
                except Exception as e:
                    logger.debug(f"Could not parse {date_field} value '{value}': {e}")
                    
        # Clean up redundant fields
        for field in ['path', 'frontmatter', 'source']:
            standardized.pop(field, None)
            
        return standardized
        
    def _compute_embedding(self, text: str) -> List[float]:
        """Generate embedding for text"""
        return self.embed_model.embed_query(text)
        
    def process_document(self, file_path: str) -> Optional[ProcessedDocument]:
        """Process a document file and return ProcessedDocument object"""
        try:
            loader = self._create_loader(file_path)
            documents = loader.load()
            
            if not documents:
                logger.warning(f"No content loaded from {file_path}")
                return None
                
            chunks = self.text_splitter.split_documents(documents)
            processed_chunks = []
            
            for chunk in chunks:
                metadata = self._standardize_metadata(chunk.metadata)
                metadata['file_path'] = file_path  # Ensure file_path is set
                
                processed_chunk = ProcessedDocument(
                    content=chunk.page_content,
                    metadata=metadata,
                    uuid=self._generate_uuid(chunk.page_content, metadata),
                    embedding=self._compute_embedding(chunk.page_content)
                )
                processed_chunks.append(processed_chunk)
                
            # Create parent document
            full_content = "\n\n".join(doc.page_content for doc in documents)
            parent_metadata = self._standardize_metadata(documents[0].metadata)
            parent_metadata['file_path'] = file_path
            
            return ProcessedDocument(
                content=full_content,
                metadata=parent_metadata,
                uuid=self._generate_uuid(full_content, parent_metadata),
                chunks=processed_chunks
            )
            
        except Exception as e:
            logger.error(f"Error processing document {file_path}: {str(e)}")
            return None
            
    def rerank_documents(self, query: str, documents: List[ProcessedDocument], top_k: int = None) -> List[ProcessedDocument]:
        """Rerank documents using cross-encoder if available"""
        if not self.reranker or not documents:
            return documents
            
        tokenizer, model = self.reranker
        pairs = [f"{query} [SEP] {doc.content}" for doc in documents]
        
        inputs = tokenizer(
            pairs,
            padding=True,
            truncation=True,
            return_tensors="pt",
            max_length=512
        ).to(self.config.DEVICE)
        
        with torch.no_grad():
            scores = model(**inputs).logits.cpu().numpy()
            
        # Sort documents by score
        ranked_docs = [doc for _, doc in sorted(zip(scores, documents), reverse=True)]
        
        return ranked_docs[:top_k] if top_k else ranked_docs
