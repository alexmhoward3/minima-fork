# Tech Context

## Technologies used
- Python backend with:
  - LangChain for document loading and parsing
  - ObsidianLoader for Markdown/Obsidian handling
  - HuggingFace transformers
  - python-dotenv for environment configuration
  - FastAPI with uvicorn (hot reload enabled)
- Docker for containerization and development
  - Live reload enabled for Python files
  - Environment variables passed from .env
  - Volume mounts for local development
- Qdrant vector database with payload support
- BAAI/bge-m3 reranker model
- GPU acceleration frameworks (MPS/CUDA)

## Development setup
- Docker-based development environment with hot reload
  - Changes to Python files automatically reload the service
  - No rebuild needed unless requirements.txt or Dockerfile changes
- Environment configuration via .env file:
  - LOCAL_FILES_PATH: Path to Obsidian vault
  - EMBEDDING_MODEL_ID: HuggingFace model for embeddings
  - EMBEDDING_SIZE: Size of embedding vectors
  - START_INDEXING: Whether to start indexing on startup
  - RERANKER_MODEL: Model for reranking results
  - CHUNK_SIZE: Document chunk size
  - CHUNK_OVERLAP: Overlap between chunks
  - CHUNK_STRATEGY: Chunking strategy (h2 or character)
- Qdrant configuration and schema setup
- ObsidianLoader setup for vault parsing

## Technical constraints
- Must handle large document collections
- GPU memory requirements for model loading
- Chunk size/overlap balance for optimal search
- Hardware acceleration availability affects performance
- Obsidian metadata extraction needs to handle:
  - Frontmatter
  - Inline tags
  - Internal links
  - Creation/modification dates
