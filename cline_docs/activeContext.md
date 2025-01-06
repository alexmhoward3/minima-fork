# Active Context

## What you're working on now
Chunking strategy

## Recent changes
- Improved ObsidianLoader integration:
  - Switched to using built-in metadata extraction
  - Proper handling of tags from both frontmatter and inline
  - Standardized timestamp handling with ISO format
  - Removed redundant custom metadata extraction
  - Better type checking for different metadata formats
- Fixed document loading process:
  - Proper document splitting after loading
  - Preserved ObsidianLoader's metadata handling
  - Improved error handling and logging
- Modified the `file_path` metadata to correctly include the full file path and filename.
- Implemented H2-based chunking strategy with 800 chunk size and 100 overlap (selected via .env)

## Next steps
- Modify the reranker input to use proper separator tokens between the query and document content.
- Modify the MCP query tool to return multiple results instead of just one.
  - Add a `top_k` parameter to the `Query` model in `mcp-server/src/minima/server.py`.
  - Modify the `call_tool` function in `mcp-server/src/minima/server.py` to handle multiple results and format the output.
  - Update the `find` method in `indexer/indexer.py` to return multiple results based on the `top_k` parameter.
  - Modify `indexer/app.py` to pass the `top_k` parameter to the `indexer.find` method.
  - The `top_k` parameter should be passed as a string.
  - The `find` method in `indexer/indexer.py` should handle the dictionary input correctly.
  - The `output` in `indexer.py` should be a list of strings.
  - The `call_tool` function in `server.py` should handle the list of strings correctly.
  - The `document_store.search` method in `indexer.py` expects a string as input.
  
# Active Context

## What you're working on now
Chunking strategy

## Recent changes
- Improved ObsidianLoader integration:
  - Switched to using built-in metadata extraction
  - Proper handling of tags from both frontmatter and inline
  - Standardized timestamp handling with ISO format
  - Removed redundant custom metadata extraction
  - Better type checking for different metadata formats
- Fixed document loading process:
  - Proper document splitting after loading
  - Preserved ObsidianLoader's metadata handling
  - Improved error handling and logging
- Modified the `file_path` metadata to correctly include the full file path and filename.
- Implemented H2-based chunking strategy with 800 chunk size and 100 overlap (selected via .env)

## Next steps
- Modify the reranker input to use proper separator tokens between the query and document content.
