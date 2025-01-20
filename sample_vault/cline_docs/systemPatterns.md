# System Patterns

## How the system is built
The system uses a containerized Python backend with FastAPI for searching and indexing. The indexing system incorporates advanced reranking capabilities using the BAAI/bge-m3 model and Obsidian-specific features for enhanced document relationships.

## Development Patterns
- Hot reload development workflow:
  - Python files watched by uvicorn
  - Automatic service restart on changes
  - Docker volume mounts for live code updates
  - Environment variables from .env file
- Configuration management:
  - Central .env file for all settings
  - Environment variables passed through docker-compose
  - Settings validated at runtime
  - Docker build args for model configuration

## Key technical decisions
- Enhanced Qdrant utilization:
  - Vector embeddings with cosine similarity
  - Payload storage for Obsidian features
  - Custom scoring for relationship weighting
- Adaptive hardware acceleration (MPS -> CUDA -> CPU fallback)
- Document chunking strategy:
  - Configurable via environment variables
  - H2 or character-based chunking
  - Customizable chunk size and overlap
  - Obsidian syntax preservation
- BAAI/bge-m3 integration for semantic reranking
- HuggingFace embeddings pipeline for vector generation
- Obsidian parser for extracting structured features
- Improved metadata handling for relevance scoring
  - Explanation: The relevance scoring is implemented in the find method of indexer/indexer.py. After performing a similarity search, the system calculates a relevance score for each document based on its metadata. The score is increased for recent documents (based on the modified_at date) and for documents that have tags. Additionally, if a reranker model is configured, the results are sorted based on the reranker scores before the metadata-based relevance scoring is applied.
- Deduplication of search results

## Architecture patterns
- Container-based microservices:
  - Isolated services per responsibility
  - Live reload for development
  - Production/development parity
- Enhanced vector search pipeline:
  - Semantic similarity scoring
  - Payload-based filtering and boosting
  - Feature-weighted result ranking
- Adaptive compute resource utilization
- Chunked document processing with metadata preservation
  - Tags as filterable attributes
  - YAML frontmatter as structured payload
- Environment-based configuration:
  - Centralized .env file
  - Runtime variable validation
  - Service-specific overrides
