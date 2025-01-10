import logging
import torch
from typing import List, Dict, Optional
from datetime import datetime
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams
from langchain_qdrant import QdrantVectorStore

from .document_processing import DocumentProcessor, ProcessedDocument
from .config import config
from .models import SearchResult, SearchMatch, SearchMetadata, SearchContext
from .exceptions import SearchError, ProcessingError

logger = logging.getLogger(__name__)

class SearchService:
    """Handles document search and retrieval using Qdrant"""
    
    def __init__(
        self,
        collection_name: str = "mnm_storage",
        qdrant_host: str = "localhost",
        qdrant_port: int = 6333
    ):
        self.collection_name = collection_name
        self.config = config
        self.doc_processor = DocumentProcessor(self.config)
        self.qdrant_client = QdrantClient(host=qdrant_host, port=qdrant_port)
        self.vector_store = self._setup_vector_store()
        
    def _setup_vector_store(self) -> QdrantVectorStore:
        """Initialize or connect to Qdrant vector store"""
        if not self.qdrant_client.collection_exists(self.collection_name):
            self.qdrant_client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.config.EMBEDDING_SIZE,
                    distance=Distance.COSINE
                ),
            )
            
        return QdrantVectorStore(
            client=self.qdrant_client,
            collection_name=self.collection_name,
            embedding=self.doc_processor._initialize_embeddings()
        )
        
    def _create_search_context(self, content: str, window_size: int = 200) -> SearchContext:
        """Create context window around content"""
        return SearchContext(
            before=content[:window_size],
            after=content[-window_size:]
        )
        
    def _calculate_relevance_score(self, doc: ProcessedDocument) -> float:
        """Calculate relevance score based on document metadata"""
        score = 1.0
        
        # Boost score for recent documents
        if doc.modified_at:
            days_old = (datetime.now() - doc.modified_at).days
            score += max(0, (30 - days_old) / 30)  # Higher score for newer docs
            
        # Boost score for documents with tags
        if doc.tags:
            score += 0.5
            
        return score
        
    async def search(self, query: str, limit: int = 5) -> SearchResult:
        """Search for documents matching the query"""
        try:
            start_time = datetime.now()
            
            # Get initial results from vector store
            raw_results = self.vector_store.search(query, search_type="similarity")
            
            if not raw_results:
                return SearchResult(
                    matches=[],
                    total_matches=0,
                    query=query,
                    execution_time=0.0
                )
                
            # Convert to ProcessedDocument objects
            documents = [
                ProcessedDocument(
                    content=doc.page_content,
                    metadata=doc.metadata,
                    uuid=self.doc_processor._generate_uuid(doc.page_content, doc.metadata),
                    embedding=None  # We don't need to store the embedding here
                )
                for doc in raw_results
            ]
            
            # Rerank if reranker is available
            if self.doc_processor.reranker:
                documents = self.doc_processor.rerank_documents(query, documents, limit)
                
            # Create search matches with context and metadata
            matches = []
            seen_contents = set()
            
            for doc in documents:
                # Skip duplicate content
                if doc.content in seen_contents:
                    continue
                seen_contents.add(doc.content)
                
                # Calculate relevance score
                relevance_score = self._calculate_relevance_score(doc)
                
                match = SearchMatch(
                    content=doc.content,
                    metadata=SearchMetadata(
                        tags=doc.tags,
                        created_at=doc.created_at.isoformat() if doc.created_at else None,
                        modified_at=doc.modified_at.isoformat() if doc.modified_at else None,
                        relevance_score=relevance_score
                    ),
                    context=self._create_search_context(doc.content)
                )
                matches.append(match)
                
            # Sort by relevance score
            matches.sort(key=lambda x: x.metadata.relevance_score, reverse=True)
            
            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return SearchResult(
                matches=matches[:limit],
                total_matches=len(matches),
                query=query,
                execution_time=execution_time
            )
            
        except Exception as e:
            logger.error(f"Search error: {str(e)}")
            raise SearchError(f"Search failed: {str(e)}")
            
    async def process_document(self, file_path: str) -> Optional[ProcessedDocument]:
        """Process a document and store it in the vector store"""
        try:
            processed_doc = self.doc_processor.process_document(file_path)
            if not processed_doc or not processed_doc.chunks:
                return None
                
            # Add chunks to vector store
            for chunk in processed_doc.chunks:
                self.vector_store.add_documents(
                    documents=[Document(
                        page_content=chunk.content,
                        metadata=chunk.metadata
                    )],
                    ids=[chunk.uuid]
                )
                
            return processed_doc
            
        except Exception as e:
            logger.error(f"Processing error: {str(e)}")
            raise ProcessingError(f"Document processing failed: {str(e)}")
