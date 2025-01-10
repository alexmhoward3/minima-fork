# Minima MCP Server

A Model Context Protocol (MCP) server that provides document search and retrieval capabilities.

## Configuration

The server can be configured using environment variables. Here are the available configuration options:

### Qdrant Configuration
- `QDRANT_HOST` - Qdrant server host (default: "localhost")
- `QDRANT_PORT` - Qdrant server port (default: 6333)
- `QDRANT_COLLECTION` - Collection name (default: "mnm_storage")
- `QDRANT_PREFER_GRPC` - Use gRPC instead of HTTP (default: false)
- `QDRANT_TIMEOUT` - Request timeout in seconds (default: 10.0)

### Path Configuration
- `LOCAL_FILES_PATH` - Path to local files on host system
- `CONTAINER_PATH` - Path to files in container (default: "/usr/src/app/local_files/")
- `IGNORE_FILE` - Name of ignore file (default: ".minimaignore")

### Model Configuration
- `EMBEDDING_MODEL_ID` - Hugging Face model ID (default: "sentence-transformers/all-mpnet-base-v2")
- `EMBEDDING_SIZE` - Embedding vector size (default: 768)
- `RERANKER_MODEL` - Optional reranker model ID
- `DEVICE` - Device to run models on (e.g., "cuda", "cpu")

### Processing Configuration
- `CHUNK_SIZE` - Document chunk size (default: 800)
- `CHUNK_OVERLAP` - Overlap between chunks (default: 100)
- `CHUNK_STRATEGY` - Chunking strategy (default: "h2")
- `MAX_DOCUMENTS` - Maximum documents to process (default: 1000)
- `BATCH_SIZE` - Batch size for processing (default: 10)

### Logging Configuration
- `LOG_LEVEL` - Logging level (default: "INFO")
- `LOG_FILE` - Log file path (default: "app.log")
- `LOG_FORMAT` - Log message format

### Server Configuration
- `SERVER_NAME` - Server name (default: "minima")
- `SERVER_VERSION` - Server version (default: "0.0.1")
- `SERVER_HOST` - Server host (default: "0.0.0.0")
- `SERVER_PORT` - Server port (default: 8000)
- `SERVER_WORKERS` - Number of workers (default: 1)
- `DEBUG` - Enable debug mode (default: false)

## Example Configuration

Create a `.env` file with your desired settings:

```env
# Qdrant settings
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_COLLECTION=my_documents

# File paths
LOCAL_FILES_PATH=/path/to/your/files
CONTAINER_PATH=/usr/src/app/files

# Model settings
EMBEDDING_MODEL_ID=sentence-transformers/all-mpnet-base-v2
EMBEDDING_SIZE=768
DEVICE=cuda

# Processing settings
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
CHUNK_STRATEGY=h2

# Logging
LOG_LEVEL=INFO
LOG_FILE=minima.log

# Server
DEBUG=true
```

## Usage

1. Set up your configuration using environment variables
2. Start the server:
   ```bash
   python -m minima.server
   ```

3. The server will be available for MCP clients to connect and use its search capabilities.

## Architecture

The server uses a simplified architecture that directly connects to Qdrant for vector storage and search:

```
Claude -> MCP Server -> Qdrant
```

This eliminates unnecessary HTTP communication layers and provides better performance.