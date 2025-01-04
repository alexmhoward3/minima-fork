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
- Modified the `file_path` metadata to correctly include the full file path and filename.

## Next steps
- Decision made to not include backlinks in node metadata for now due to complexity and performance concerns. Will revisit if needed.
- Modify the reranker input to use proper separator tokens between the query and document content.
- Wikilink extraction still needs work.
- Decision made to use a fixed chunk size of 1500 characters with an overlap of 200 characters as a starting point. This approach provides a balance between simplicity and effectiveness, and will be re-evaluated as needed. Shorter notes will be handled by creating chunks that are shorter than the maximum size, without any padding.
