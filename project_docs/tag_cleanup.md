# Tag System Cleanup

## Overview
Current tag system needs to capture both frontmatter and inline tags while removing redundant path-based tags. The system should preserve tag hierarchy and clean up duplicates.

## Files Impacted
1. `indexer/indexer.py`
   - Primary location of tag processing logic
   - Contains document processing and metadata handling

2. `indexer/app.py` 
   - Handles search result processing and tag filtering
   - May need minor updates to tag handling in search results

## Implementation Details

### Tag Sources

The system needs to capture tags from two sources:

1. **Frontmatter Tags**
   - YAML format at the top of files
   - Can be single string: `tags: tag1`
   - Can be array: `tags: [tag1, tag2]`
   - Can be multiline:
     ```yaml
     tags:
       - tag1
       - tag2
     ```

2. **Inline Tags**
   - Written in document content as `#tag`
   - Can include hierarchy: `#folder/tag`
   - Can appear anywhere in the content
   - Should be extracted using ObsidianLoader's `TAG_REGEX`

### Required Changes

1. **Tag Processing Function**
   ```python
   def _process_file(self, loader):
       if isinstance(loader, ObsidianLoader):
           tags = set()
           
           # Process frontmatter tags
           if 'tags' in doc.metadata:
               frontmatter_tags = doc.metadata['tags']
               if isinstance(frontmatter_tags, str):
                   tags.add(frontmatter_tags.strip())
               elif isinstance(frontmatter_tags, (list, set)):
                   tags.update(t.strip() for t in frontmatter_tags if isinstance(t, str))
           
           # Process inline tags from content
           content_tags = self._extract_inline_tags(doc.page_content)
           tags.update(content_tags)
           
           # Clean all collected tags
           clean_tags = self._clean_tags(tags)
           
           # Update metadata with cleaned tags
           doc.metadata['tags'] = clean_tags
   ```

2. **Inline Tag Extraction**
   ```python
   def _extract_inline_tags(self, content: str) -> Set[str]:
       """Extract inline tags from document content."""
       tags = set()
       # Use ObsidianLoader's TAG_REGEX to find inline tags
       for match in re.finditer(ObsidianLoader.TAG_REGEX, content):
           tag = match.group(1)  # Extract tag without '#' prefix
           if tag:
               tags.add(tag)
       return tags
   ```

3. **Tag Cleaning and Validation**
   ```python
   def _clean_tags(self, tags: Set[str]) -> List[str]:
       """
       Clean and validate tags from both frontmatter and inline sources.
       Preserves hierarchical structure while removing invalid/path-based tags.
       """
       cleaned = set()
       for tag in tags:
           # Skip empty tags
           if not tag or not tag.strip():
               continue
           
           # Clean the tag
           tag = tag.strip('#').strip()
           
           # Skip if tag is invalid
           if not self._validate_tag(tag):
               continue
           
           # Skip if tag is derived from file path
           if self._is_path_based_tag(tag):
               continue
           
           cleaned.add(tag)
       
       return sorted(list(cleaned))
   
   def _validate_tag(self, tag: str) -> bool:
       """Validate if a tag is legitimate."""
       invalid_patterns = ['.md', '.txt', '\\', ' ']  # Allow forward slashes for hierarchy
       return not any(pattern in tag for pattern in invalid_patterns)
   
   def _is_path_based_tag(self, tag: str) -> bool:
       """Check if tag is derived from file path or name."""
       filepath = self.current_file_path  # Need to track current file being processed
       return (
           tag in filepath or
           tag.lower() in filepath.lower() or
           tag in filepath.split('/') or
           f"{tag}.md" in filepath
       )
   ```

### Implementation Steps

1. **Add Inline Tag Support**
   - Implement `_extract_inline_tags` using ObsidianLoader's TAG_REGEX
   - Add test cases for various inline tag formats
   - Verify hierarchical inline tags are preserved

2. **Update Tag Processing**
   - Combine frontmatter and inline tags
   - Remove all automatic tag generation from paths
   - Preserve hierarchical structure of tags
   - Add tracking of current file path for validation

3. **Search Result Processing**
   - Update deep_search to handle combined tag sources
   - Ensure tag filtering works with hierarchical structure
   - Remove any remaining path-based tag logic

## Testing Strategy

1. **Unit Tests**
   - Frontmatter tag processing (all formats)
   - Inline tag extraction
   - Tag cleaning and validation
   - Hierarchical tag preservation
   - Path-based tag removal
   - Edge cases:
     * Empty tags
     * Malformed tags
     * Mixed frontmatter and inline tags
     * Duplicate tags from different sources

2. **Integration Tests**
   - Full document processing
   - Search with tag filtering
   - Hierarchical tag queries
   - Combined source tag handling

## Success Criteria
1. Both frontmatter and inline tags are captured
2. Hierarchical tags preserved from both sources
3. No path-based or filename tags
4. No duplicate tags in final output
5. All tests passing

## Timeline
1. Tag Processing Cleanup: 2-3 days
2. ObsidianLoader Integration: 1-2 days
3. Search Result Handling: 1 day
4. Testing and Validation: 1-2 days

Total estimated time: 4-6 days

## Risks and Mitigation

1. **Risk**: Performance impact from inline tag scanning
   - Mitigation: Cache tag extraction results
   - Mitigation: Optimize regex pattern matching

2. **Risk**: Tag source conflicts
   - Mitigation: Clear precedence rules for duplicates
   - Mitigation: Preserve both sources in metadata if needed

3. **Risk**: Edge cases in hierarchical tags
   - Mitigation: Comprehensive testing
   - Mitigation: Clear validation rules for hierarchy