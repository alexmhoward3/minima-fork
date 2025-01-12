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
I'd like to ensure that changes to my obsidian vault are reflected in the qdrant vector database. I've experimented with a complex file watching mechanism, but it wasn't reliably detecting changes in the Obsidian vault
It was struggling with path mappings between Windows and the Docker container
The file watcher approach had multiple points of failure

Solution Design
Instead of real-time file watching, i'd like to implement a much simpler polling-based solution that:

Periodically scans the vault directory (every 5 minutes, 20 seconds to start for testing)
Compares file modification timestamps
Only re-indexes files that have changed
Stores the last indexed time in Qdrant metadata

Key Changes
Add a new poll_for_changes() method to indexer.py that checks for modified files
Create a new poller.py with a simple polling loop

However, i'm getting an error in the logs: 2025-01-11 22:46:43 indexer-1  | INFO:     Waiting for application startup.
2025-01-11 22:49:22 indexer-1  | 2025-01-12 04:49:22,790 - indexer - ERROR - Error updating last indexed time for /usr/src/app/local_files/Work/03-Resources/Meetings/2024-12-19 Annemarie 1 to 1.md: 'QdrantClient' object has no attribute 'update_points'
2025-01-11 22:49:24 indexer-1  | 2025-01-12 04:49:24,055 - indexer - ERROR - Error updating last indexed time for /usr/src/app/local_files/Personal/03_Resources/Notetaking/Workflow from book highlights.md: 'QdrantClient' object has no attribute 'update_points'
2025-01-11 22:49:24 indexer-1  | 2025-01-12 04:49:24,572 - indexer - ERROR - Error updating last indexed time for /usr/src/app/local_files/Work/01-Projects/Hong Kong Trip/HK article.md: 'QdrantClient' object has no attribute 'update_points'
</task>