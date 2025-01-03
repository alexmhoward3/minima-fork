# Tech Context

## Technologies used
- Python backend with HuggingFace transformers
- Docker for containerization
- Qdrant vector database with payload support
- BAAI/bge-m3 reranker model
- GPU acceleration frameworks (MPS/CUDA)
- Markdown parsing libraries with Obsidian extensions

## Development setup
- Docker-based development environment
- GPU support configuration required for acceleration
- Environment variables for model and embedding configuration
- Qdrant payload schema configuration
- Obsidian syntax parsing configuration

## Technical constraints
- System should handle large document collections
- GPU memory requirements for model loading
- Chunk size/overlap balance for optimal search
- Hardware acceleration availability affects performance
- Obsidian syntax preservation during chunking
- Payload size optimization for Obsidian metadata
- Efficient filtering and scoring with payload data
