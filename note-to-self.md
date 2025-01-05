## command to get it started: 
    docker compose -f docker-compose-mcp.yml down; docker compose -f docker-compose-mcp.yml up --build -d

obsidian-loader-test.py start:
set QDRANT_HOST=localhost; set QDRANT_PORT=6333; set START_INDEXING=true; set CONTAINER_PATH=C:\Users\Alex\Documents\Projects\sample_vault; set LOCAL_FILES_PATH=C:\Users\Alex\Documents\Projects\sample_vault; set EMBEDDING_MODEL_ID=sentence-transformers/all-mpnet-base-v2; set EMBEDDING_SIZE=768; python tests/obsidian-loader-test.py

## Inspector
npx -y @modelcontextprotocol/inspector uv --directory c:/Users/Alex/Documents/Projects/minima-fork/mcp-server run minima

## Notes
Twice now claude has recommended a healthcheck and separate Dockerfile with curl for qdrant and health check.probably a good idea because it can take a few minutes to start the qdrant server

## Next thing to try
- [x] implement ObsidianLoader, add tags and created/updated dates to qdrant payload
- [x] consider whether backlinks are necessary metadata, since they're already present in the note
  - decision: would add complexity to note parsing and not super useful in metadata. save this for another time, possibly with a knowledge graph.
- [x] play around with chunk size
- [x] hmm not pointing to vault, even though local files variable is set
- [ ] back up storage. it's completed indexing. 
- [x] re-think chunking we're at a huge storage size (20-ish gigs). Update: moved it to F drive
- [ ] how does the reranker work in the minima indexer > qdrant vector store > mcp query workflow?
- [ ] consider adding a progress bar to indexing
- [ ] STARTING THIS: the tool just returns one search result. how can we improve that?
  - i want to improve the tools available in @/mcp-server/ . First, the tool only allows a single search result. can we implement a TOP_K variable that allows the user the ability to set the number, ex TOP_K=3
- [ ] consider implementing openai embeddings
- [ ] create mcp tool to nuke the database and reindex

## DONE ObsidianLoader
This basically just parses frontmatter, tags and dataview (?). Capturing links in notes might have to be a parsing regex - Update: decided not to do this

## Appendix 
### Qdrant Dockerfile reasoning 
Let me explain the benefits of the healthcheck and custom Dockerfile approach:

Reliability Benefits:
Docker's health check provides system-level verification that Qdrant is truly ready to accept connections
The health check ensures not just that the container is running, but that the service inside is actually responding
This is more robust than application-level retry logic alone, as it prevents the indexer from even starting until Qdrant is confirmed healthy
Monitoring Benefits:
Docker will track the health status of Qdrant, making it easier to diagnose issues
The health status can be viewed through Docker commands and monitoring tools
Container orchestration tools can use this health information for better management
Maintenance Benefits:
Having curl in the container makes it easier to troubleshoot issues by allowing direct HTTP requests to Qdrant
Curl can be used for manual health checks and API testing when debugging
The custom Dockerfile documents the addition of debugging tools
Scalability Benefits:
In a production environment, orchestration tools like Kubernetes can use the health check for:
Readiness probes (knowing when to send traffic)
Liveness probes (knowing when to restart)
Auto-healing (automatically restarting unhealthy containers)