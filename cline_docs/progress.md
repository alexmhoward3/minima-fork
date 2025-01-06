# Progress

## What works
- Basic indexing functionality
- File ignoring via .minimaignore
- BAAI/bge-m3 reranker implementation
- Improved ObsidianLoader integration:
  - Built-in metadata extraction
  - Tag parsing from frontmatter and inline
  - Proper timestamp handling
  - Standardized metadata format
- Enhanced search with metadata relevance scoring
- Configurable chunking strategy (size, overlap, character or H2)

## What's left to build
- Improve cross-document relevance
- Add diversity scoring for results
- Optimize reranker token handling
- Modify the MCP query tool to return multiple results instead of just one.
  - Tried adding a `top_k` parameter to the `Query` model in `mcp-server/src/minima/server.py`.
  - Tried modifying the `call_tool` function in `mcp-server/src/minima/server.py` to handle multiple results and format the output.
  - Tried updating the `find` method in `indexer/indexer.py` to return multiple results based on the `top_k` parameter.
  - Tried modifying `indexer/app.py` to pass the `top_k` parameter to the `indexer.find` method.
  - Encountered a `TypeError: 'dict' object has no attribute 'replace'` in `indexer.py`.
  - The `top_k` parameter should be passed as a string.
  - The `find` method in `indexer/indexer.py` should handle the dictionary input correctly.
  - The `output` in `indexer.py` should be a list of strings.
  - The `call_tool` function in `server.py` should handle the list of strings correctly.
  - The `document_store.search` method in `indexer.py` expects a string as input.
  
# Progress

## What works
- Basic indexing functionality
- File ignoring via .minimaignore
- BAAI/bge-m3 reranker implementation
- Improved ObsidianLoader integration:
  - Built-in metadata extraction
  - Tag parsing from frontmatter and inline
  - Proper timestamp handling
  - Standardized metadata format
- Enhanced search with metadata relevance scoring
- Configurable chunking strategy (size, overlap, character or H2)

## What's left to build
- Improve cross-document relevance
- Add diversity scoring for results
- Optimize reranker token handling

## Progress status
The project has completed major improvements in metadata handling and document processing.
