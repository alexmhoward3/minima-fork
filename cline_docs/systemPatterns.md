# System Patterns

## How the system is built
The system is built with a Python backend for indexing and a frontend for searching. The indexing system incorporates advanced reranking capabilities using the BAAI/bge-m3 model and Obsidian-specific features for enhanced document relationships.

## Key technical decisions
- Enhanced Qdrant utilization:
  - Vector embeddings with cosine similarity
  - Payload storage for Obsidian features
  - Custom scoring for relationship weighting
- Adaptive hardware acceleration (MPS -> CUDA -> CPU fallback)
- Document chunking strategy with Obsidian syntax preservation, chunk size and overlap configurable via environment variables
- BAAI/bge-m3 integration for semantic reranking
- HuggingFace embeddings pipeline for vector generation
- Obsidian parser for extracting structured features
- Improved metadata handling for relevance scoring
  - Explanation: The relevance scoring is implemented in the find method of indexer/indexer.py. After performing a similarity search, the system calculates a relevance score for each document based on its metadata. The score is increased for recent documents (based on the modified_at date) and for documents that have tags. Additionally, if a reranker model is configured, the results are sorted based on the reranker scores before the metadata-based relevance scoring is applied.
- Deduplication of search results

## Architecture patterns
- Microservices architecture for scalability
- Enhanced vector search pipeline:
  - Semantic similarity scoring
  - Payload-based filtering and boosting
  - Feature-weighted result ranking
- Adaptive compute resource utilization
- Chunked document processing with metadata preservation
  - Tags as filterable attributes
  - YAML frontmatter as structured payload