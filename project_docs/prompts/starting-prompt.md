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
I want to implement a Deep Search tool in the MCP server.py. This tool will allow formatted query structures for things like 
Temporal queries ("from this week")
Summarization requests ("summarize my meeting notes")
Topic clustering ("what topics have I been writing about lately?")
Trend analysis ("how has my thinking about X evolved?")

THERE WILL BE NO PARSING OF NATURAL LANGUAGE. MCP allows llms like claude access to databases, so Claude will:
Parse out that this is a temporal query
Calculate the relevant date range (e.g., current week's start to now)
Format a structured query that tells the indexer to:
a) Get documents within that date range
b) Format them appropriately
c) Return them to me for summarization

I have the tool set up and created, but tags don't appear to be working. for ex: 

Alex@Alex-Desktop MINGW64 ~/Documents/Projects/minima-fork (working-branch-restart-2)
$ curl http://localhost:8001/query/deep -X POST -H "Content-Type: application/json" -d '{
    "query": "content",
    "mode": "summary",
    "start_date": "2024-01-01T00:00:00",
    "end_date": "2025-01-10T23:59:59",
    "include_raw": true
}'
{"analysis":"Here's a summary of the documents found:\n\n- **Content & Product:**\n\n1. Consumers don't care whether they're consuming is content or product; it's one thing.\n2. Content strategy:\n\t+ Edit stat all of workflows.\n\t+ User exp these contents.\n3. Book...\n\n- Lonely plant content is the way in which we deliver proof of change, it's how we present our identity, have already done a lot of that - guidebooks, digital content, social. Now our product. Our conte...\n\n- ### Content & Product\nconsumers don't care whether that they 're consuming is content or product . it's one thing Content strategy \n-  edit stat all of \n-  user exp these \n-  workflows \n-  content str...\n\n","metadata":{"total_documents":3,"date_range":"2024-01-01 00:00:00 to 2025-01-10 23:59:59","tags":"no tag filter"},"raw_results":[{"content":"**Content & Product:**\n\n1. Consumers don't care whether they're consuming is content or product; it's one thing.\n2. Content strategy:\n\t+ Edit stat all of workflows.\n\t+ User exp these contents.\n3. Books aren't the product; it's the content in them.\n4. Expertise t insight are the product.\n\n**Content Supply Chain:**\n\n1. Does that redefine what a book is?\n2. Yes.\n3. Spa :fy: I don't think about buying an album, I think about paying subscription.\n4. Neil: I'm going to look for something short tax.\n\n**Purpose of Content: Alignment**\n\n1. Good news: we all agree.\n2. Think intuitively Personalization current topic tugs ④ n articles collecting data via cohesion.","metadata":{"file_path":"C:\\Users\\Alex\\OneDrive\\Apps\\remotely-save\\Obsidian Vault.trash/EPAM- D-is 2.md","tags":[],"links":[],"created_at":"2024-11-05T20:28:00","modified_at":"2024-11-06T02:28:35.856275","relevance_score":1.0}},{"content":"Lonely plant content is the way in which we deliver proof of change, it's how we present our identity, have already done a lot of that - guidebooks, digital content, social. Now our product. Our content is how people see and exp LP as a brand, our contributors are a key part of that.","metadata":{"file_path":"C:\\Users\\Alex\\OneDrive\\Apps\\remotely-save\\Obsidian VaultWork/03-Resources/Final contributor notes for presentation.md","tags":[],"links":[],"created_at":"2024-02-27T19:38:00","modified_at":"2024-03-24T23:52:12","relevance_score":1.0}},{"content":"### Content & Product\nconsumers don't care whether that they 're consuming is content or product . it's one thing Content strategy \n-  edit stat all of \n-  user exp these \n-  workflows \n-  content structure we've often though \n-  about + lose as different things Not building a 4×15 but a content supply chains\n\nBooks aren't the product ; its the content in them \n-  expertise t insight are the product \n-  Also not just text \n-  what's the balance of production for the future ? \n-  video , and :O , photo Paul : Beware of trying to make the website a singular thing . Contributors are central \n-  their experience could be better \n-  how do people become a","metadata":{"file_path":"C:\\Users\\Alex\\OneDrive\\Apps\\remotely-save\\Obsidian Vault.trash/EPAM- D-is.md","tags":[],"links":[],"created_at":"2024-11-05T20:26:00","modified_at":"2024-11-06T02:27:56.545029","relevance_score":1.0}}]}


curl $ curl http://localhost:8001/query/deep -X POST -H "Content-Type: application/json" -d '{
    "query": "content",
    "mode": "summary",
    "start_date": "2024-01-01T00:00:00",
    "end_date": "2025-01-10T23:59:59",
    "tags": ["Resource/meetings"],
    "include_raw": true
}'
{"analysis":"","metadata":{"total_documents":0,"date_range":"2024-01-01 00:00:00 to 2025-01-10 23:59:59","tags":["Resource/meetings"]},"raw_results":[]} 
{"analysis":"","metadata":{"total_documents":0,"date_range":"2024-01-01 00:00:00 to 2025-01-10 23:59:59","tags":["meeting"]},"raw_results":[]}

in the docker logs, i see this: 
2025-01-10 21:57:39 indexer-1     | INFO:app:Normalized doc tags: set()
2025-01-10 21:57:39 indexer-1     | INFO:app:Normalized request tags: {'resource/meetings'}
2025-01-10 21:57:39 indexer-1     | INFO:app:Document tags don't match required tags, skipping


It seems like it filters out anything that doesn't precisely match the tags. 

</task>