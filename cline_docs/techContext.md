# Tech Context

## Technologies used
- Python backend with:
  - LangChain for document loading and parsing
  - ObsidianLoader for Markdown/Obsidian handling
  - HuggingFace transformers
- Docker for containerization
- Qdrant vector database with payload support
- BAAI/bge-m3 reranker model
- GPU acceleration frameworks (MPS/CUDA)
  - FastAPI for creating the API endpoints
  - Uvicorn as the ASGI server
  - Pydantic for data validation and settings management
  - Custom tools for document summarization, timeline generation, topic extraction, and trend analysis
  - Integration with MCP for tool exposure
- python-multipart for parsing multipart form data

## Development setup
- Docker-based development environment
- GPU support configuration required for acceleration
- Environment variables for model and embedding configuration
- Qdrant payload schema configuration
- Obsidian syntax parsing through LangChain

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
