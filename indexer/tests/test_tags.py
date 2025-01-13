import pytest
from pathlib import Path
from indexer.indexer import Indexer

def test_is_path_based_tag():
    indexer = Indexer()
    
    # Test with simple filename
    assert indexer._is_path_based_tag("test", "/path/to/test.md") == True
    
    # Test with path component
    assert indexer._is_path_based_tag("path", "/path/to/file.md") == True
    
    # Test with non-matching tag
    assert indexer._is_path_based_tag("unrelated", "/path/to/file.md") == False
    
    # Test with hierarchical path
    assert indexer._is_path_based_tag("to", "/path/to/file.md") == True
    
    # Test with case differences
    assert indexer._is_path_based_tag("PATH", "/path/to/file.md") == True
    
def test_process_tags():
    indexer = Indexer()
    
    # Test with frontmatter tags
    metadata = {
        "file_path": "/path/to/test.md",
        "tags": ["valid-tag", "path", "test"],
        "inline_tags": {"inline-tag", "path"}
    }
    
    tags = indexer._process_tags(metadata)
    assert "valid-tag" in tags
    assert "inline-tag" in tags
    assert "path" not in tags  # Should be removed as path-based
    assert "test" not in tags  # Should be removed as path-based
    
    # Test with hierarchical tags
    metadata = {
        "file_path": "/path/to/test.md",
        "tags": ["folder/tag"],
        "inline_tags": {"category/subcategory"}
    }
    
    tags = indexer._process_tags(metadata)
    assert "folder/tag" in tags
    assert "category/subcategory" in tags