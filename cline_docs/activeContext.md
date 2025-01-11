# Active Context

## What you're working on now
Updating documentation to reflect the new document summarization and analysis tools.

## Recent changes
- Added new tools for document summarization and analysis:
  - `document_summary`: Provides a concise summary of key documents.
  - `document_timeline`: Generates a chronological timeline of documents.
  - `document_topics`: Groups documents by topics/tags.
  - `document_trends`: Analyzes document frequency over time.
  - `query`: Allows basic semantic search across local files.
  - `deep_search`: Enables advanced search with filtering and analysis.
- These tools are implemented in `mcp-server/src/minima/tools/` and integrated into the MCP server.
- Updated `indexer/app.py` and `indexer/indexer.py` to support the new analysis modes.
- Modified `mcp-server/src/minima/requestor.py` to handle requests to the new endpoints.
- Updated `mcp-server/src/minima/server.py` to expose the new tools via MCP.

## Next steps
- Update the rest of the `cline_docs/` files to reflect the new functionality.
- Test the new tools thoroughly.
- Consider adding more advanced analysis capabilities.
