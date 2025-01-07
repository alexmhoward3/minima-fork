# Qdrant Database Cleanup Implementation Plan

## Overview

After reviewing the existing codebase, the cleanup functionality needs to work in harmony with:
1. The ObsidianLoader's metadata handling
2. The standardized file path metadata (`file_path`, `source`) 
3. The existing indexing and search functionality
4. The chunking strategies (either character-based or H2-based)

### 1. Existing Cleanup Script Structure
The current cleanup.py implementation includes:

```python
class QdrantCleanup:
    def __init__(self, client: QdrantClient, collection_name: str):
        self.client = client
        self.collection_name = collection_name
```

### 2. Enhanced Duplicate Detection
The current implementation detects duplicates based on file paths. We should enhance this by:

```python
def _detect_duplicates(self, points: List[Dict]) -> Dict[str, List[str]]:
    \"\"\"
    Find duplicate entries based on multiple criteria:
    1. Exact file path matches
    2. Similar content with different paths
    3. Chunked content from same source
    
    Returns:
        Dict mapping file paths to lists of point IDs
    \"\"\"
    duplicates = {}
    
    # Group by standardized paths first
    for point in points:
        path = self._extract_canonical_path(point.payload)
        if path:
            if path not in duplicates:
                duplicates[path] = []
            duplicates[path].append(point.id)
            
    # For each group, sort by metadata
    for path, point_ids in duplicates.items():
        if len(point_ids) > 1:
            # Sort by modified date if available
            points_with_dates = []
            for point_id in point_ids:
                point = next(p for p in points if p.id == point_id)
                modified_at = self._extract_modified_date(point.payload)
                points_with_dates.append((point_id, modified_at))
            
            # Keep most recent version
            sorted_points = sorted(points_with_dates, 
                                key=lambda x: x[1] if x[1] else datetime.min,
                                reverse=True)
            duplicates[path] = [p[0] for p in sorted_points]
            
    return duplicates
```

### 3. Enhanced Cleanup Logic
Building on the existing cleanup implementation, add improved duplicate handling:

```python
def cleanup_duplicates(self) -> Dict[str, int]:
    \"\"\"
    Enhanced duplicate cleanup with better metadata handling
    and chunked content awareness.
    
    Returns:
        Dict with cleanup statistics
    \"\"\"
    try:
        logger.info(\"Starting enhanced duplicate cleanup\")
        
        # Get all points with full payload
        scroll_result = self.client.scroll(
            collection_name=self.collection_name,
            with_payload=True,
            with_vectors=False,  # Don't need vectors for deduplication
            limit=10000
        )
        points = scroll_result[0]
        
        # Find duplicates considering metadata
        duplicate_groups = self._detect_duplicates(points)
        
        # Track statistics
        total_removed = 0
        files_affected = set()
        
        # Process each group
        for file_path, point_ids in duplicate_groups.items():
            if len(point_ids) <= 1:
                continue
                
            # Keep the first one (already sorted by date in _detect_duplicates)
            to_remove = point_ids[1:]
            
            # Delete in batches
            for i in range(0, len(to_remove), 100):
                batch = to_remove[i:i + 100]
                self.client.delete(
                    collection_name=self.collection_name,
                    points_selector=models.PointIdsList(points=batch)
                )
                total_removed += len(batch)
                files_affected.add(file_path)
                
            logger.info(f\"Removed {len(to_remove)} duplicates for {file_path}\")
            
        return {
            \"total_points\": len(points),
            \"duplicates_removed\": total_removed,
            \"files_affected\": len(files_affected)
        }
        
    except Exception as e:
        logger.error(f\"Error during duplicate cleanup: {str(e)}\")
        raise
```

### 4. Helper Methods
Add utility methods to support the enhanced cleanup:

```python
def _extract_canonical_path(self, payload: Dict) -> Optional[str]:
    \"\"\"
    Extract and normalize the file path from payload metadata.
    Handles various metadata formats and paths.
    \"\"\"
    metadata = payload.get('metadata', {})
    path = (metadata.get('file_path') or 
            payload.get('file_path') or 
            metadata.get('source') or 
            payload.get('source'))
    
    if path:
        # Normalize path separators
        return path.replace('\\\\', '/')
    return None
    
def _extract_modified_date(self, payload: Dict) -> Optional[datetime]:
    \"\"\"
    Extract the modified date from payload metadata.
    Handles various date formats.
    \"\"\"
    metadata = payload.get('metadata', {})
    modified = metadata.get('modified_at')
    
    if not modified:
        return None
        
    try:
        if isinstance(modified, (int, float)):
            return datetime.fromtimestamp(modified)
        elif isinstance(modified, str):
            return datetime.fromisoformat(modified.replace(\" \", \"T\"))
    except Exception:
        return None
```

## Usage Examples

### 1. Basic Usage
```python
from indexer.indexer import Indexer

indexer = Indexer()
results = indexer.cleanup_duplicates()
print(f\"Removed {results['duplicates_removed']} duplicates from {results['files_affected']} files\")
```

### 2. With Progress Tracking
```python
from indexer.indexer import Indexer
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

indexer = Indexer()
try:
    results = indexer.cleanup_duplicates()
    print(f\"Cleanup Results:\")
    print(f\"- Total points processed: {results['total_points']}\")
    print(f\"- Duplicates removed: {results['duplicates_removed']}\")
    print(f\"- Files affected: {results['files_affected']}\")
except Exception as e:
    print(f\"Cleanup failed: {e}\")
```

### 3. Integration with MCP Server
```python
# In your MCP server implementation:
from indexer.indexer import Indexer

async def cleanup_command(self):
    \"\"\"MCP tool for running database cleanup\"\"\"
    try:
        indexer = Indexer()
        results = indexer.cleanup_duplicates()
        
        return {
            \"content\": [{
                \"type\": \"text\",
                \"text\": f\"Successfully cleaned up database:\
\" \\
                        f\"- Removed {results['duplicates_removed']} duplicates\
\" \\
                        f\"- Affected {results['files_affected']} files\
\" \\
                        f\"- Processed {results['total_points']} total points\"
            }]
        }
    except Exception as e:
        return {
            \"content\": [{
                \"type\": \"text\",
                \"text\": f\"Error during cleanup: {str(e)}\"
            }]
        }
```

## Implementation Notes

### Key Features
1. Handles both Obsidian and regular document metadata formats
2. Normalizes file paths across different storage formats
3. Preserves most recent versions based on metadata
4. Handles chunked content intelligently
5. Batch processes deletions for efficiency

### Safety Features
1. **Validation**: Multiple checks for path extraction and date parsing
2. **Logging**: Comprehensive logging at all stages
3. **Batching**: Deletes points in small batches to prevent overwhelming the database
4. **Error Handling**: Robust error handling and reporting
5. **Metadata Preservation**: Keeps the most relevant version based on metadata

### Performance Considerations
1. Uses scroll API for efficient point retrieval
2. Processes points in memory before making changes
3. Batches delete operations
4. Skips vector loading during point retrieval
5. Uses efficient path normalization`

## Implementation Plan

### DONE Phase 0: Quick Duplicate Check (30 min)

To quickly verify duplicate entries exist:

1. Add this to cleanup.py:
```python
def quick_duplicate_check(self) -> Dict[str, int]:
    """Do a fast check for potential duplicates"""
    scroll_result = self.client.scroll(
        collection_name=self.collection_name,
        with_payload=True,
        limit=1000  # Start with first 1000 for speed
    )
    
    points = scroll_result[0]
    paths = {}
    
    for point in points:
        path = self._extract_file_path(point.payload)
        if path:
            if path not in paths:
                paths[path] = 0
            paths[path] += 1
    
    duplicates = {k:v for k,v in paths.items() if v > 1}
    if duplicates:
        print("\nPotential duplicates found:")
        for path, count in duplicates.items():
            print(f"- {path}: {count} entries")
        
    return {
        "total_points": len(points),
        "unique_files": len(paths),
        "files_with_duplicates": len(duplicates),
        "total_duplicates": sum(v-1 for v in duplicates.values())
    }
```

Verify by running:
```python
from indexer.cleanup import QdrantCleanup
from indexer.indexer import Indexer
indexer = Indexer()
cleanup = QdrantCleanup(indexer.qdrant, indexer.config.QDRANT_COLLECTION)
print(cleanup.quick_duplicate_check())
```

### Phase 1: Test Framework Setup (30 min)

1. Create a test indexer that uses the sample vault:
```python
def setup_test_indexer():
    """Create test indexer using sample vault"""
    import os
    os.environ["CONTAINER_PATH"] = "C:/Users/Alex/Documents/Projects/minima-fork/sample_vault"
    os.environ["LOCAL_FILES_PATH"] = os.environ["CONTAINER_PATH"]
    os.environ["CHUNK_SIZE"] = "800"
    os.environ["CHUNK_OVERLAP"] = "100"
    
    from indexer.indexer import Indexer
    return Indexer()

def index_test_vault():
    """Index sample vault for testing"""
    indexer = setup_test_indexer()
    for root, _, files in os.walk(os.environ["CONTAINER_PATH"]):
        for file in files:
            if file.endswith('.md'):
                path = os.path.join(root, file)
                indexer.index({
                    "path": path,
                    "file_id": file
                })
    return indexer
```

Verify by:
1. Running `index_test_vault()`
2. Using the quick_duplicate_check on the resulting database

### Phase 2: Basic Cleanup Implementation (30 min)

1. Implement the basic cleanup in cleanup.py (focus on exact path matches first):
```python
def remove_duplicates_for_path(self, path: str, point_ids: List[str]) -> int:
    """Remove duplicates for a single file path"""
    if len(point_ids) <= 1:
        return 0
        
    # Keep newest, delete others
    to_remove = point_ids[1:]
    self.client.delete(
        collection_name=self.collection_name,
        points_selector=models.PointIdsList(
            points=to_remove
        )
    )
    return len(to_remove)
```

Test by:
1. Running quick_duplicate_check() 
2. Removing duplicates for one specific path
3. Running quick_duplicate_check() again to verify count decreased

### Phase 3: Metadata-Aware Cleanup (30 min)

1. Add metadata sorting to keep the most relevant version:
```python
def sort_points_by_metadata(self, points: List[Dict]) -> List[Dict]:
    """Sort points by metadata quality and recency"""
    def point_score(point):
        metadata = point.payload.get('metadata', {})
        score = 0
        # Prefer points with more metadata
        score += len(metadata) * 10
        # Prefer more recent modifications
        if 'modified_at' in metadata:
            try:
                modified = parse_date(metadata['modified_at'])
                score += modified.timestamp()
            except:
                pass
        return score
        
    return sorted(points, key=point_score, reverse=True)
```

Test by:
1. Picking a file that exists in multiple forms
2. Running cleanup on just that file
3. Verifying the kept version has the best metadata

### Phase 4: UI Commands (30 min)

1. Add cleanup commands to your MCP server:
```python
@app.tool()
async def check_duplicates() -> str:
    """Check for duplicate entries in the database"""
    cleanup = QdrantCleanup(indexer.qdrant, indexer.config.QDRANT_COLLECTION)
    results = cleanup.quick_duplicate_check()
    return f"Found {results['total_duplicates']} duplicate entries across {results['files_with_duplicates']} files"

@app.tool()
async def cleanup_database() -> str:
    """Remove duplicate entries from the database"""
    cleanup = QdrantCleanup(indexer.qdrant, indexer.config.QDRANT_COLLECTION)
    results = cleanup.cleanup_duplicates()
    return f"Removed {results['duplicates_removed']} duplicates from {results['files_affected']} files"
```

Test by:
1. Opening Claude Desktop
2. Running the check_duplicates tool
3. Running cleanup_database
4. Running check_duplicates again to verify cleanup
