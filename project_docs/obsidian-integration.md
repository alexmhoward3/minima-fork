# ObsidianLoader Integration in Minima

This document describes how Minima integrates with Obsidian markdown files using LangChain's ObsidianLoader, focusing on path handling and metadata extraction.

## Overview

The integration handles two key aspects:
1. Directory-based loading with proper path resolution
2. Tag extraction from both frontmatter and inline content

## Path Handling

### Directory-Based Loading

ObsidianLoader works differently from other loaders - it loads files from a directory rather than individual files. To handle this:

1. Initialization:
   ```python
   loader = ObsidianLoader(path=CONTAINER_PATH, collect_metadata=True)
   ```
   - Uses container root path to access all markdown files
   - Enables metadata collection for frontmatter parsing

2. Path Resolution:
   ```python
   # Convert relative paths to absolute
   if not os.path.isabs(source):
       source = os.path.join(CONTAINER_PATH, source)
   
   # Normalize paths for comparison
   source_path = os.path.normpath(source)
   target_path = os.path.normpath(file_path)
   ```
   - Handles both absolute and relative paths
   - Normalizes paths for cross-platform compatibility

3. Document Matching:
   ```python
   # Try both exact match and relative path match
   if source_path == target_path or source_path.endswith(rel_path):
       documents.append(doc)
   ```
   - Supports multiple path matching strategies
   - Ensures correct document selection

## Tag Processing

### 1. Frontmatter Tags

Global tags from YAML frontmatter are extracted and applied to all chunks from a document:

```python
if 'tags' in doc.metadata:
    tags = doc.metadata['tags']
    if isinstance(tags, str):
        # Use ObsidianLoader's TAG_REGEX to extract tags
        matches = ObsidianLoader.TAG_REGEX.finditer(tags)
        tags = [match.group(1) for match in matches if match]
    doc.metadata['global_tags'] = tags
```

Example frontmatter:
```yaml
---
tags:
  - dailynote
  - work
---
```
These tags are stored in the `global_tags` metadata field and apply to all chunks from this document.

### 2. Inline Tags

Tags within document content are extracted and stored per chunk:

```python
content_matches = ObsidianLoader.TAG_REGEX.finditer(doc.page_content)
inline_tags = [match.group(1) for match in content_matches if match]
if inline_tags:
    doc.metadata['inline_tags'] = inline_tags
```

Example inline tag:
```markdown
Today I took William on a #bike ride.
```
The #bike tag is stored in the `inline_tags` metadata field of only the chunk containing this text.

## Document Processing Flow

1. Load all documents from container path
2. Filter for target file using path matching
3. Split matched document into chunks
4. Process tags for each chunk:
   - Add global tags from frontmatter
   - Extract inline tags from chunk content
5. Store documents in Qdrant with metadata

## Metadata Structure

Each document chunk in Qdrant contains:
- `file_path`: Full path to source file
- `global_tags`: Tags from frontmatter (if any)
- `inline_tags`: Tags found in chunk content (if any)
- Original metadata from ObsidianLoader

## Benefits

1. **Proper Path Resolution**: Handles complex directory structures and path variations
2. **Granular Tag Context**: Preserves both document-level and chunk-level tag information
3. **Metadata Preservation**: Maintains all Obsidian-specific metadata
4. **Flexible Matching**: Supports multiple path matching strategies for reliability

## Future Improvements

1. Support for Obsidian-specific features:
   - Backlinks
   - Aliases
   - Hierarchical tags
2. Enhanced metadata extraction:
   - Custom frontmatter fields
   - Block references
   - Dataview metadata
