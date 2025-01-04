command to get it started: 
    docker compose -f docker-compose-mcp.yml down; docker compose -f docker-compose-mcp.yml up --build -d

obsidian-loader-test.py start:
set QDRANT_HOST=localhost; set QDRANT_PORT=6333; set START_INDEXING=true; set CONTAINER_PATH=C:\Users\Alex\Documents\Projects\sample_vault; set LOCAL_FILES_PATH=C:\Users\Alex\Documents\Projects\sample_vault; set EMBEDDING_MODEL_ID=sentence-transformers/all-mpnet-base-v2; set EMBEDDING_SIZE=768; python tests/obsidian-loader-test.py

## Inspector
npx -y @modelcontextprotocol/inspector uv --directory c:/Users/Alex/Documents/Projects/minima-fork/mcp-server run minima

## DONE ObsidianLoader
This basically just parses frontmatter, tags and dataview (?). Capturing links in notes might have to be a parsing regex. Update: decided not to do this

## Next thing to try
- [x] implement ObsidianLoader, add tags and created/updated dates to qdrant payload
- [x] consider whether backlinks are necessary metadata, since they're already present in the note
  - decision: would add complexity to note parsing and not super useful in metadata. save this for another time, possibly with a knowledge graph.
- [ ] play around with chunk size
- [ ] how does the reranker work in the minima indexer > qdrant vector store > mcp query workflow?
- [ ] the tool just returns one search result. how can we improve that?
- [ ] consider implementing openai embeddings
- [ ] create mcp tool to nuke the database and reindex