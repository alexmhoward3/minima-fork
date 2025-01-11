I'm working on a RAG system that uses the model context protocol to allow Claude access to my Obsidian notes. It uses containers to run 1. qdrant for vector storage and 2. indexer.py for embedding and search. Below is an overview, a list of features and the key files, and a task I want you to complete. Before moving onto the task, use filesystem to review the files.

<overview>
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
</overview>

<features>
An .env file contains: 
LOCAL_FILES_PATH="C:\Users\Alex\OneDrive\Apps\remotely-save\Obsidian Vault"
EMBEDDING_MODEL_ID=sentence-transformers/all-mpnet-base-v2
EMBEDDING_SIZE=768
START_INDEXING=true 
RERANKER_MODEL=BAAI/bge-m3
CHUNK_SIZE=800
CHUNK_OVERLAP=100
CHUNK_STRATEGY=h2
</features>

<files>
The key files are here:
C:\Users\Alex\Documents\Projects\minima-fork\indexer\indexer.py
C:\Users\Alex\Documents\Projects\minima-fork\indexer\app.py
C:\Users\Alex\Documents\Projects\minima-fork\indexer\async_queue.py
C:\Users\Alex\Documents\Projects\minima-fork\indexer\async_loop.py
C:\Users\Alex\Documents\Projects\minima-fork\indexer\Dockerfile
C:\Users\Alex\Documents\Projects\minima-fork\mcp-server\src\minima\requestor.py
C:\Users\Alex\Documents\Projects\minima-fork\mcp-server\src\minima\server.py
C:\Users\Alex\Documents\Projects\minima-fork\docker-compose-mcp.yml
</files>

<task>
I want to replace the HTTP-based indexer service with direct MCP integration.
Looking at the current setup:

indexer.py contains the core document processing and search functionality
app.py exposes this via HTTP endpoints
Both use Qdrant directly

The simplest path forward would be to:

Keep the core Indexer class from indexer.py - it's well-written and handles all the document processing
Remove the HTTP layer (app.py and FastAPI)
Write a minimal MCP server that directly uses the Indexer class

Here's the simplified plan:
1. In mcp-server/:
   - Copy over indexer.py 
   - Create minimal server.py that:
     a) Initializes the Indexer
     b) Creates MCP handlers that call Indexer methods
     c) No HTTP, just direct MCP <-> Indexer communication

2. Remove:
   - app.py (FastAPI)
   - HTTP-related code
   - Complex folder structures
   - Extra abstraction layers

3. Keep existing:
   - Document processing logic
   - Qdrant integration
   - File watching if needed

This gives us the a simplified workflow (Claude -> MCP -> Qdrant) but with:

Minimal code changes
No unnecessary abstractions
Direct path to migrate functionality
</task>