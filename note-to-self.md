command to get it started: 
    docker compose -f docker-compose-mcp.yml down; docker compose -f docker-compose-mcp.yml up --build -d

obsidian-loader-test.py start:
set QDRANT_HOST=localhost; set QDRANT_PORT=6333; set START_INDEXING=true; set CONTAINER_PATH=C:\Users\Alex\Documents\Projects\sample_vault; set LOCAL_FILES_PATH=C:\Users\Alex\Documents\Projects\sample_vault; set EMBEDDING_MODEL_ID=sentence-transformers/all-mpnet-base-v2; set EMBEDDING_SIZE=768; python tests/obsidian-loader-test.py

## Inspector
npx -y @modelcontextprotocol/inspector uv --directory c:/Users/Alex/Documents/Projects/minima-fork/mcp-server run minima

## ObsidianLoader
This basically just parses frontmatter, tags and dataview (?). Capturing links in notes might have to be a parsing regex. 

## Next thing to try
- implement ObsidianLoader, add tags and created/updated dates to qdrant payload
- consider whether backlinks are necessary metadata, since they're already present in the note
- play around with chunk size

## possible future tasks
Some good improvements in the roadmap doc.
consider implementing openai embeddings
create mcp tool to nuke the database and reindex