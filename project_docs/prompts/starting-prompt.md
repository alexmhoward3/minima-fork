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
  - Tags for content categorization
  - YAML frontmatter for structured metadata
  - Hierarchical tags for taxonomy
  - Backlinks for reverse relationship tracking (deferred for future implementation)
- Allow users to search using Obsidian syntax and features
- Respect ignore files to prevent indexing of unwanted documents
- Use document relationships to improve search relevance
</overview>

<files>

## Project Structure
```
C:\\Users\\Alex\\Documents\\Projects\\minima-fork\\indexer\\
├── app.py: Main application file that sets up a FastAPI server, defines API routes for querying and embedding, and schedules indexing tasks.
├── async_loop.py: Contains functions for crawling the specified directory and enqueuing files for indexing (`crawl_loop`), and for processing the queue and indexing the files (`index_loop`).
├── async_queue.py: Defines an asynchronous queue (`AsyncQueue`) for communication between the crawling and indexing processes.
├── Dockerfile: Defines the Docker image for the indexer application, setting up a Python 3.11 environment, installing dependencies, and specifying the command to run the application.
├── ignore_patterns.py: Loads ignore patterns from the .minimaignore file
├── indexer.py: Defines the `Indexer` class, which handles the core indexing logic, including initializing the Qdrant vector store, setting up the embedding model, and providing methods for indexing, purging, and searching documents.
├── requirements.txt: Lists the Python dependencies for the indexer application.
├── singleton.py: Defines a `Singleton` metaclass that ensures only one instance of a class is created.
└── storage.py: Defines the data models and storage logic using SQLModel, including functions for creating the database, adding, deleting, and querying documents, and checking if a file needs reindexing.

C:\\Users\\Alex\\Documents\\Projects\\minima-fork\\mcp-server\\
├── pyproject.toml: Project configuration file for the MCP server.
├── README.md: Documentation for the MCP server.
├── uv.lock: Lock file for the project's dependencies.
└── src/
    └── minima/
        ├── __init__.py: Defines the main entry point for the package, running the MCP server's main function.
        ├── requestor.py: Defines a function `request_data` that sends a POST request to the indexer's `/query` endpoint to retrieve data based on a given query.
        └── server.py: Defines the MCP server using the `mcp` library, setting up logging, defining a `Query` model, and implementing `list_tools`, `list_prompts`, `call_tool`, and `get_prompt` functions for handling MCP requests.

C:\Users\Alex\Documents\Projects\minima-fork\docker-compose-mcp.yml
C:\Users\Alex\Documents\Projects\minima-fork\.env
├──user adjusted variables like local files location, embedding model, chunk size and overlap, etc
```
</files>
<coding_parameters>
All code should follow best practices of modularity, separation of concerns, error handling and logging. Keep code files under 250 words and specific to key areas. Development is done by an AI coder, so modularity is key. When modifying code use the EDIT_TOOL to avoid rewriting code.
</coding_parameters>

<task>
I've implemented chunk size and overlap in my environment variables, and I want to add h2 chunking. I've created chunking.py, but indexer isn't reading it when i start up the container. 
C:\Users\Alex\Documents\Projects\minima-fork\indexer\chunking.py
 </task>
