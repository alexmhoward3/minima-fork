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
I've implemented a Deep Search tool in the MCP server.py, but I want to refactor the tools there into separate tools. I've written up an implementation plan C:\Users\Alex\Documents\Projects\minima-fork\project_docs\clarifying-tools.md. I'm in the process of phase 1, but i'm having trouble with some errors: 

Traceback (most recent call last): File "C:\Users\Alex\Documents\Projects\minima-fork\mcp-server\.venv\Lib\site-packages\mcp\server\stdio.py", line 83, in stdio_server
yield read_stream, write_stream File "C:\Users\Alex\Documents\Projects\minima-fork\mcp-server\src\minima\server.py", line 218, in main
InitializationOptions( ^^^^^^^^^^^^^^^^^^^^^ NameError: name 'InitializationOptions' is not defined. Did you mean: 'NotificationOptions'? During handling of the above exception, another exception occurred: + Exception Group Traceback (most recent call last): | File "<frozen runpy>", line 198, in _run_module_as_main | File "<frozen runpy>", line 88, in _run_code | File "C:\Users\Alex\Documents\Projects\minima-fork\mcp-server\.venv\Scripts\minima.exe\__main__.py", line 8, in <module>
| File "C:\Users\Alex\Documents\Projects\minima-fork\mcp-server\src\minima\__init__.py", line 11, in main
| asyncio.run(server.main()) | File "C:\Users\Alex\AppData\Local\Programs\Python\Python312\Lib\asyncio\runners.py", line 194, in run
| return runner.run(main)
| ^^^^^^^^^^^^^^^^ | File "C:\Users\Alex\AppData\Local\Programs\Python\Python312\Lib\asyncio\runners.py", line 118, in run
| return self._loop.run_until_complete(task) | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ | File "C:\Users\Alex\AppData\Local\Programs\Python\Python312\Lib\asyncio\base_events.py", line 687, in run_until_complete
| return future.result()
| ^^^^^^^^^^^^^^^ | File "C:\Users\Alex\Documents\Projects\minima-fork\mcp-server\src\minima\server.py", line 214, in main
| async with mcp.server.stdio.stdio_server() as (read_stream, write_stream): | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ | File "C:\Users\Alex\AppData\Local\Programs\Python\Python312\Lib\contextlib.py", line 231, in __aexit__ | await self.gen.athrow(value) | File "C:\Users\Alex\Documents\Projects\minima-fork\mcp-server\.venv\Lib\site-packages\mcp\server\stdio.py", line 80, in stdio_server
| async with anyio.create_task_group() as tg:
| ^^^^^^^^^^^^^^^^^^^^^^^^^ | File "C:\Users\Alex\Documents\Projects\minima-fork\mcp-server\.venv\Lib\site-packages\anyio\_backends\_asyncio.py", line 763, in __aexit__
| raise BaseExceptionGroup( | ExceptionGroup: unhandled errors in a TaskGroup (1 sub-exception) +-+---------------- 1 ---------------- | Traceback (most recent call last): | File "C:\Users\Alex\Documents\Projects\minima-fork\mcp-server\.venv\Lib\site-packages\mcp\server\stdio.py", line 83, in stdio_server
| yield read_stream, write_stream
| File "C:\Users\Alex\Documents\Projects\minima-fork\mcp-server\src\minima\server.py", line 218, in main | InitializationOptions( | ^^^^^^^^^^^^^^^^^^^^^
| NameError: name 'InitializationOptions' is not defined. Did you mean: 'NotificationOptions'? +------------------------------------


The aim is to refactor the tools and make the tools clear for LLM use. They should keep operations focused and atomic. 

First review the implementation plan, then review the necessary files. When you've done that, we can begin with the first step.
</task>