# Active Context

## What you're working on now
Refining ObsidianLoader integration and metadata handling.

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

## Next steps
- Modify the reranker input to use proper separator tokens between the query and document content.
