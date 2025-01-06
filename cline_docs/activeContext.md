# Active Context

## What you're working on now
- Implementing multiple results in MCP query tool
- Optimizing chunking strategy implementation

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
- Modified the `file_path` metadata to correctly include the full file path and filename
- Implemented H2-based chunking strategy with 800 chunk size and 100 overlap (selected via .env)
- Fixed bug in Search Tool results extraction from indexer response

## Next steps
- Modify the reranker input to use proper separator tokens between query and document content
- Complete multiple results implementation:
  - Add `top_k` parameter to Query model
  - Update tool execution to handle multiple results
  - Modify indexer find method for multiple results
  - Fix type handling issues in parameter passing
- Implement diversity scoring for search results
- Improve cross-document relevance scoring
