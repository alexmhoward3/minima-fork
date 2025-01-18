# Qdrant Sync Implementation Plan

## Overview
This plan details the implementation of a sync system to keep Qdrant's vector database in sync with changes to the Obsidian vault. Two implementation approaches are provided: a comprehensive solution and a simplified quick-start solution.

## Simplified Implementation
For quick deployment and testing, this simplified approach can be implemented in a few hours:

```python
async def check_for_changes(self):
    """Simple periodic check for file changes"""
    current_files = {}
    
    # Scan files and get basic metadata
    for root, _, files in os.walk(self.config.CONTAINER_PATH):
        for file in files:
            if not file.endswith('.md'):  # Only check markdown files
                continue
            
            path = os.path.join(root, file)
            try:
                stat = os.stat(path)
                current_files[path] = stat.st_mtime
            except:
                continue

    # Get existing files from Qdrant
    results = self.qdrant.scroll(
        collection_name=self.config.QDRANT_COLLECTION,
        limit=10000
    )
    
    if not results or not results[0]:
        # Nothing in Qdrant yet, index everything
        for path in current_files:
            self.index({"path": path, "file_id": str(uuid.uuid4())})
        return

    # Build map of existing files in Qdrant
    indexed_files = {}
    for point in results[0]:
        if 'metadata' in point.payload and 'file_path' in point.payload['metadata']:
            path = point.payload['metadata']['file_path']
            mtime = point.payload['metadata'].get('modified_at_timestamp', 0)
            indexed_files[path] = mtime

    # Check for changes
    for path, mtime in current_files.items():
        if path not in indexed_files or abs(indexed_files[path] - mtime) > 1:
            # File is new or modified, reindex it
            self.index({"path": path, "file_id": str(uuid.uuid4())})

    # Check for deletions
    for path in indexed_files:
        if path not in current_files:
            # File was deleted, remove from Qdrant
            self.qdrant.delete(
                collection_name=self.config.QDRANT_COLLECTION,
                points_filter=Filter(
                    must=[FieldCondition(key="metadata.file_path", match={"text": path})]
                )
            )
```

Add to app.py:
```python
async def run_indexer():
    indexer = Indexer()
    
    while True:
        try:
            await indexer.check_for_changes()
        except Exception as e:
            print(f"Error checking for changes: {e}")
        await asyncio.sleep(60)  # Check every minute

if __name__ == "__main__":
    asyncio.run(run_indexer())
```

### Simplified Implementation Benefits
- Quick to implement (2-3 hours)
- Simple modification time comparison
- Basic error handling
- Minimal configuration needed
- Works with Docker volumes
- No complex state tracking

### Simplified Implementation Limitations
- May reindex files unnecessarily
- No batching of operations
- Basic error handling only
- No performance optimizations
- No progress tracking
- Limited monitoring capabilities

## Comprehensive Implementation
If more robust functionality is needed later, the following sections detail a more complete implementation...

This plan details the implementation of a sync system to keep Qdrant's vector database in sync with changes to the Obsidian vault. The solution uses Qdrant's native indexing and upsert capabilities to efficiently track and handle file changes.

## Core Concept
- Use Qdrant's payload indexing to track file metadata
- Implement batched upsert operations for efficient updates
- Use content-based UUIDs to handle duplicates and changes
- Employ periodic scanning with metadata comparison
- Process changes in batches for optimal performance

## Milestones

### 1. Set Up Metadata Indexing
**Context**: We need to add file tracking metadata to Qdrant's payload indexing system.

Tasks:
1. Add new index fields to collection setup:
   ```python
   # Required fields: file_path, modified_at_timestamp, file_size
   # Test by verifying indexes exist via Qdrant API
   ```
2. Create test documents with metadata
3. Verify metadata is properly indexed

Expected Outcome:
- All file metadata fields are indexed
- Field queries return expected results
- Payload schema verification passes

### 2. Implement Content-Based UUID Generation
**Context**: We need a reliable way to track unique document chunks.

Tasks:
1. Create UUID generation function:
   ```python
   # Must account for: content, file_path, modified_at, tags
   # Test with identical and modified content
   ```
2. Add UUID generation to document processing
3. Test UUID consistency across operations

Expected Outcome:
- Same content produces same UUID
- Modified content produces different UUID
- UUIDs are properly stored in Qdrant

### 3. Implement File Change Detection
**Context**: Need efficient way to detect file changes by comparing metadata.

Tasks:
1. Create efficient directory scanning:
   ```python
   # Must handle large directories
   # Must respect .minimaignore
   # Test with various file sizes and counts
   ```
2. Implement metadata comparison logic
3. Add batching for large directories
4. Create change detection tests

Expected Outcome:
- Reliably detects added/modified/deleted files
- Handles large directories efficiently
- Respects ignore patterns
- Memory usage stays consistent

### 4. Implement Batched Upsert Operations
**Context**: Need to handle changes efficiently with proper error handling.

Tasks:
1. Implement batch processing:
   ```python
   # Define optimal batch size
   # Add progress tracking
   # Test with various batch sizes
   ```
2. Add retry logic for failed operations
3. Implement error handling
4. Create upsert operation tests

Expected Outcome:
- Operations are properly batched
- Failed operations are retried
- Errors are properly handled and logged
- Performance metrics are captured

### 5. Implement Change Processing Loop
**Context**: Need to periodically check and process changes.

Tasks:
1. Create async change detection loop:
   ```python
   # Add configurable check interval
   # Must handle shutdown gracefully
   # Test with simulated changes
   ```
2. Add operation logging
3. Implement recovery mechanisms
4. Create integration tests

Expected Outcome:
- Changes are detected and processed reliably
- System recovers from failures
- Operations are properly logged
- Resource usage is optimized

### 6. Add Monitoring and Logging
**Context**: Need visibility into sync operations.

Tasks:
1. Add structured logging:
   ```python
   # Log operations, timing, errors
   # Add batch performance metrics
   # Test log output format
   ```
2. Create operation metrics
3. Implement health checks
4. Add monitoring endpoints

Expected Outcome:
- All operations are logged
- Performance metrics are captured
- Health status is exposed
- Logs are properly structured

## Test Plan

### Unit Tests
1. UUID Generation
   - Test consistency
   - Test with modifications
   - Test with empty content

2. Change Detection
   - Test file additions
   - Test file modifications
   - Test file deletions
   - Test with ignore patterns

3. Batch Processing
   - Test batch size limits
   - Test error handling
   - Test retry logic
   - Test partial failures

### Integration Tests
1. Full Sync Cycle
   - Test complete sync process
   - Test with large directories
   - Test recovery from failures

2. Performance Tests
   - Test with 1000+ files
   - Test memory usage
   - Test CPU usage
   - Test batch processing speed

## Acceptance Criteria
1. System detects and processes all file changes
2. Changes are processed within 1 minute of occurrence
3. Memory usage remains stable
4. CPU usage remains below 50%
5. All operations are properly logged
6. System recovers from failures automatically
7. No data loss occurs during sync

## Dependencies
1. Qdrant with payload indexing support
2. Python 3.9+
3. AsyncIO support
4. Sufficient system resources for batch processing

## Rollout Plan
1. Implement in development environment
2. Run full test suite
3. Deploy to staging with sample vault
4. Monitor for 24 hours
5. Deploy to production
6. Monitor metrics and logs

## Fallback Plan
If issues occur:
1. System logs error and continues
2. Failed operations are retried
3. Manual sync can be triggered
4. Previous version can be restored

## Notes for Implementers
- Start with small batch sizes and adjust based on performance
- Log extensively during initial deployment
- Monitor memory usage carefully
- Test with representative data volumes
- Follow error handling patterns in existing code
- Use existing logging configuration
- Reference existing indexer implementation for patterns