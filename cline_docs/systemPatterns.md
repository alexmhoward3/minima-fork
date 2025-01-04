# System Patterns

## How the system is built
The system is built with a Python backend for indexing and a frontend for searching. The indexing system incorporates advanced reranking capabilities using the BAAI/bge-m3 model and Obsidian-specific features for enhanced document relationships.

## Key technical decisions
- Enhanced Qdrant utilization:
  - Vector embeddings with cosine similarity
  - Payload storage for Obsidian features
  - Custom scoring for relationship weighting
- Adaptive hardware acceleration (MPS -> CUDA -> CPU fallback)
- Document chunking strategy (500 size/200 overlap) with Obsidian syntax preservation
- BAAI/bge-m3 integration for semantic reranking
- HuggingFace embeddings pipeline for vector generation
- Obsidian parser for extracting structured features
- Improved metadata handling for relevance scoring
- Deduplication of search results

## Architecture patterns
- Microservices architecture for scalability
- Enhanced vector search pipeline:
  - Semantic similarity scoring
  - Payload-based filtering and boosting
  - Feature-weighted result ranking
- Adaptive compute resource utilization
- Chunked document processing with metadata preservation
  - Obsidian feature integration:
  - Internal links stored in payload (requires regex parsing)
  - Tags as filterable attributes
  - YAML frontmatter as structured payload
  - Backlinks tracked in payload metadata (deferred for future implementation)
