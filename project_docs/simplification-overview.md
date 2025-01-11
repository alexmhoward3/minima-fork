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