# EPUB Support Implementation Plan

## Overview
This document outlines how to add EPUB support to the existing RAG system using Langchain's EPubLoader. The implementation will preserve book structure and metadata while integrating with the existing vector store system.

## Prerequisites

### System Dependencies
```bash
# Ubuntu/Debian
apt-get install pandoc

# MacOS
brew install pandoc

# Windows
choco install pandoc
```

### Python Dependencies
Add to requirements.txt:
```
langchain
pandoc
```

## Implementation Steps

### 1. Update Indexer Configuration

In indexer.py, add EPUB support to the Config class:

```python
from langchain_community.document_loaders import EPubLoader

class Config:
    EXTENSIONS_TO_LOADERS = {
        # ... existing loaders ...
        ".epub": EPubLoader,
    }
    
    # Optional: Add EPUB-specific settings
    EPUB_CHUNK_BY = "chapter"  # or "section"
```

### 2. Enhance Metadata Handling

Update _process_file method to handle EPUB-specific metadata:

```python
def _process_file(self, loader):
    # ... existing code ...
    
    if isinstance(loader, EPubLoader):
        for doc in documents:
            # Add EPUB-specific metadata
            doc.metadata.update({
                "chapter": doc.metadata.get("chapter"),
                "book_title": doc.metadata.get("title"),
                "author": doc.metadata.get("author"),
                "chapter_number": doc.metadata.get("chapter_number")
            })
```

### 3. Modify Search Function

Update find method to handle EPUB-specific features:

```python
def find(self, query: str):
    # ... existing code ...
    
    # Add EPUB-specific metadata to results
    for item in sorted_docs:
        if ".epub" in item.metadata.get("file_path", ""):
            result["epub_metadata"] = {
                "book_title": item.metadata.get("book_title"),
                "chapter": item.metadata.get("chapter"),
                "author": item.metadata.get("author")
            }
```

## Testing

### Test Cases
1. Basic EPUB loading
   - Verify chapter extraction
   - Check metadata preservation
   - Validate text content

2. Vector search testing
   - Search within single book
   - Search across multiple books
   - Verify chapter context preserved

3. Edge cases
   - Large EPUBs (>500 pages)
   - Books with complex structure
   - Invalid/corrupted EPUBs

### Sample Test Code

```python
def test_epub_loading():
    loader = EPubLoader("test_book.epub")
    docs = loader.load()
    
    assert len(docs) > 0
    assert "chapter" in docs[0].metadata
    assert docs[0].page_content != ""
```

## Environment Configuration

Add to .env:
```
EPUB_CHUNK_BY=chapter
EPUB_INCLUDE_TOC=true
EPUB_METADATA_FIELDS=title,author,chapter
```

## Usage Examples

```python
# Load and index a directory of EPUBs
async def index_epub_directory(dir_path: str):
    epub_files = Path(dir_path).glob("*.epub")
    for epub in epub_files:
        loader = EPubLoader(str(epub))
        await async_queue.put({
            "path": str(epub),
            "file_id": generate_file_id(epub)
        })

# Search across books
def search_books(query: str, author: Optional[str] = None):
    results = indexer.find(query)
    if author:
        results = [r for r in results 
                  if r.metadata.get("author") == author]
    return results
```

## Error Handling

Handle common EPUB-specific errors:
- Invalid EPUB format
- Missing metadata
- Encoding issues
- Large file handling

## Future Enhancements

1. Advanced features:
   - Table of contents integration
   - Footnote handling
   - Image extraction
   - Cross-reference preservation

2. Performance optimizations:
   - Caching of processed EPUBs
   - Batch processing for multiple books
   - Memory usage optimization

3. Search enhancements:
   - Book-specific relevance scoring
   - Chapter context preservation
   - Series/collection awareness

## Pull Request Checklist

Before submitting PR:
- [ ] pandoc dependency documented
- [ ] Basic EPUB loading works
- [ ] Metadata handling implemented
- [ ] Search function updated
- [ ] Tests passing
- [ ] Documentation updated
- [ ] Error handling in place
