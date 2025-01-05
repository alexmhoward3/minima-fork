# Active Context

## What you're working on now
Implementing TOP_K variable for multiple search results

## Recent changes
- Implemented TOP_K configuration:
  - Added TOP_K environment variable (defaults to 3)
  - Updated indexer to support multiple search results
  - Modified server response format to handle multiple results
  - Enhanced result output with content, metadata, and links
  - Added proper error handling for the new format

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
- Test TOP_K functionality with various configurations
- Consider adding sorting/filtering options for multiple results
- Modify the reranker input to use proper separator tokens between the query and document content.
