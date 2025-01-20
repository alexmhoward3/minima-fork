# Product Context

## Why this project exists
This project aims to provide a tool for indexing and searching through documents. It has connection to Claude and other LLMs via the Model Context Protocol (MCP).

## What problems it solves
- Quickly finding information within a large collection of documents
- Leveraging Obsidian's knowledge graph features for enhanced search relevance
- Understanding and utilizing document relationships through internal links and tags
- Maintaining context through metadata and backlinks

## How it should work
The system should:
- Index documents while preserving Obsidian-specific features:
  - Tags (#tag) for content categorization
  - YAML frontmatter for structured metadata
  - Hierarchical tags for taxonomy
  - Backlinks for reverse relationship tracking (deferred for future implementation)
- Allow users to search using Obsidian syntax and features
- Respect ignore files to prevent indexing of unwanted documents
- Use document relationships to improve search relevance

## Development workflow
The project uses a development-friendly setup:
- Docker-based environment with hot reload:
  - Code changes automatically trigger service restart
  - No rebuild needed for Python file changes
  - Fast feedback loop for development
- Environment-based configuration:
  - All settings in centralized .env file
  - Easy to modify without code changes
  - Consistent across development and production
- GPU acceleration when available:
  - Automatic hardware detection
  - Fallback to CPU when needed
  - Configurable via environment variables

## Deployment considerations
- Environment configuration:
  - All settings managed via .env file
  - Docker configuration through environment variables
  - Hardware-specific settings (GPU, memory)
- Volume management:
  - Obsidian vault mounting
  - Development code mounting
  - Persistent storage for Qdrant
- Resource requirements:
  - GPU access for model acceleration
  - Memory for embedding models
  - Storage for vector database

## Integration points
- Obsidian vault:
  - Direct access to markdown files
  - Metadata extraction
  - Tag and link processing
- MCP protocol:
  - Standardized query interface
  - Result formatting
  - Error handling
- Vector database:
  - Document storage
  - Similarity search
  - Metadata filtering
