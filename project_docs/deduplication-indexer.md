# Preventing Duplicates in Minima's Vector Store

## Current Problem
Currently, the indexer creates duplicate entries in Qdrant when:
1. Files are reindexed after system restarts
2. Files are modified and reindexed
3. The same content exists in multiple files

This happens because:
- We generate random UUIDs for each document chunk
- There's no check for existing entries before indexing
- No unique constraints are enforced on file paths or content

## Proposed Solution
Use deterministic IDs based on content hashing along with Qdrant's upsert functionality.

### Why This Approach?
1. Content-based hashing ensures same content gets same ID
2. Upsert automatically handles updates vs inserts
3. No need for external tracking or metadata store
4. Works with chunking since each chunk gets its own hash
5. Handles both file renames and content updates correctly

## Implementation Steps

### 1. Create Deterministic ID Generator
```python
def generate_chunk_id(file_path: str, chunk_content: str, chunk_index: int) -> str:
    """
    Generate deterministic ID for a document chunk.
    Combines file path, content, and chunk position to handle:
    - Same content in different files
    - Different chunks from same file
    - Content reordering within files
    """
    content_hash = hashlib.sha256(
        f"{file_path}:{chunk_content}:{chunk_index}".encode()
    ).hexdigest()
    return f"chunk_{content_hash}"
```

### 2. Modify Document Processing
Update `_process_file` method in `indexer.py`:
```python
def _process_file(self, loader) -> List[str]:
    try:
        documents = loader.load()
        if not documents:
            return []

        # Split documents into chunks
        if os.environ.get("CHUNK_STRATEGY") == "h2":
            chunks = []
            for doc in documents:
                split_docs = self.text_splitter.split_text(doc.page_content)
                for i, content in enumerate(split_docs):
                    chunk = type(doc)(
                        page_content=content, 
                        metadata=doc.metadata
                    )
                    chunk.metadata['chunk_index'] = i
                    chunks.append(chunk)
            documents = chunks
        else:
            documents = self.text_splitter.split_documents(documents)
            for i, doc in enumerate(documents):
                doc.metadata['chunk_index'] = i

        # Generate deterministic IDs
        ids = []
        for doc in documents:
            chunk_id = generate_chunk_id(
                doc.metadata['file_path'],
                doc.page_content,
                doc.metadata['chunk_index']
            )
            ids.append(chunk_id)

        # Use upsert instead of add_documents
        self.document_store.upsert_documents(
            documents=documents, 
            ids=ids
        )
        
        return ids
        
    except Exception as e:
        logger.error(f"Error processing file {loader.file_path}: {str(e)}")
        return []
```

### 3. Add QdrantVectorStore Extension
Create new file `vector_store.py`:
```python
from langchain_qdrant import QdrantVectorStore
from typing import List, Optional
from langchain.schema import Document

class MinimalVectorStore(QdrantVectorStore):
    def upsert_documents(
        self,
        documents: List[Document],
        ids: Optional[List[str]] = None
    ) -> List[str]:
        """
        Upsert documents into Qdrant.
        Uses points_upsert to replace existing entries.
        """
        texts = [doc.page_content for doc in documents]
        metadatas = [doc.metadata for doc in documents]
        embeddings = self.embedding.embed_documents(texts)
        
        self.client.upsert(
            collection_name=self.collection_name,
            points=[
                models.PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload={
                        "page_content": text,
                        "metadata": metadata,
                    }
                )
                for point_id, text, metadata, embedding 
                in zip(ids, texts, metadatas, embeddings)
            ]
        )
        return ids
```

### 4. Update Indexer Initialization
Modify `_setup_collection` in `indexer.py`:
```python
def _setup_collection(self) -> MinimalVectorStore:
    if not self.qdrant.collection_exists(self.config.QDRANT_COLLECTION):
        self.qdrant.create_collection(
            collection_name=self.config.QDRANT_COLLECTION,
            vectors_config=VectorParams(
                size=self.config.EMBEDDING_SIZE,
                distance=Distance.COSINE
            ),
        )
    return MinimalVectorStore(
        client=self.qdrant,
        collection_name=self.config.QDRANT_COLLECTION,
        embedding=self.embed_model,
    )
```

## Benefits
1. No duplicate entries for same content
2. Automatic handling of file updates
3. Preserves chunk ordering
4. No external state needed
5. Easy to understand and maintain
6. Minimal changes to existing code

## Future Considerations
1. May want to add batch processing for larger files
2. Could add content-based deduplication across files
3. Consider adding metadata versioning
4. May need index optimization after many updates

## Implementation Order
1. Create and test hash generation function
2. Implement vector store extension
3. Modify document processing
4. Update collection setup
5. Add tests for deduplication
6. Run cleanup on existing data