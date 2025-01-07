command to get it started: 
    docker compose -f docker-compose-mcp.yml down; docker compose -f docker-compose-mcp.yml up --build -d

obsidian-loader-test.py start:
set QDRANT_HOST=localhost; set QDRANT_PORT=6333; set START_INDEXING=true; set CONTAINER_PATH=C:\Users\Alex\Documents\Projects\sample_vault; set LOCAL_FILES_PATH=C:\Users\Alex\Documents\Projects\sample_vault; set EMBEDDING_MODEL_ID=sentence-transformers/all-mpnet-base-v2; set EMBEDDING_SIZE=768; python tests/obsidian-loader-test.py

## To restart indexer (huge)
docker compose -f docker-compose-mcp.yml restart indexer

## Test query from cmd
curl -X POST -H "Content-Type: application/json" -d "{\"query\": \"leadership\"}" http://localhost:8001/query

## Inspector
npx -y @modelcontextprotocol/inspector uv --directory c:/Users/Alex/Documents/Projects/minima-fork/mcp-server run minima

## DONE ObsidianLoader
This basically just parses frontmatter, tags and dataview (?). Capturing links in notes might have to be a parsing regex. Update: decided not to do this

## Next thing to try
- [x] implement ObsidianLoader, add tags and created/updated dates to qdrant payload
- [x] consider whether backlinks are necessary metadata, since they're already present in the note
  - decision: would add complexity to note parsing and not super useful in metadata. save this for another time, possibly with a knowledge graph.
- [x] play around with chunk size
- [x] hmm not pointing to vault, even though local files variable is set
- [ ] fix duplicate entries. FIXED - indexer now generate's persistent UUIDs. Need to check this by: 
        To test that the indexer won't duplicate files, we can try a few approaches:

        1. First, let's verify the current number of entries in your Qdrant collection:
           ```python
           client = QdrantClient(host="localhost", port=6333)
           stats = client.get_collection("mnm_storage")
           print(f"Initial count: {stats.points_count}")
           ```

        2. Then we can test for duplicates by:
           - Re-indexing the same file multiple times 
           - Checking that the point count doesn't increase
           - Verifying that files have consistent IDs across runs

        The easiest way to test would be to:

        3. Pick a specific markdown file to test with
        4. Index it
        5. Note the ID(s) generated for its chunks
        6. Re-index the same file
        7. Verify the same IDs are generated

- [ ] how does the reranker work in the minima indexer > qdrant vector store > mcp query workflow?
- [ ] consider adding a progress bar to indexing
- [ ] the tool just returns one search result. how can we improve that?
  - i want to improve the tools available in @/mcp-server/ . First, the tool only allows a single search result. can we implement a TOP_K variable that allows the user the ability to set the number, ex TOP_K=3
- [ ] consider implementing openai embeddings
- [ ] create mcp tool to nuke the database and reindex
- [ ] revisit chunking strat:
    - I'd also like to review my chunking strategy. Please review the key documents that will be indexed: 
    - Daily notes: "C:\Users\Alex\OneDrive\Apps\remotely-save\Obsidian Vault\Periodic Notes\Daily Notes\2024\11-November\2024-11-12.md"
    - Meeting notes: "C:\Users\Alex\OneDrive\Apps\remotely-save\Obsidian Vault\Work\03-Resources\Meetings\2024-01-08 PI Planning Kickoff.md"
    - Project notes: "C:\Users\Alex\OneDrive\Apps\remotely-save\Obsidian Vault\Work\01-Projects\Grand Army Discovery Sessions.md"