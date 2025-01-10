# RAG Search Results Implementation Plan

This document outlines the plan for improving the RAG search results implementation to better align with MCP best practices and provide more structured, useful results to LLMs.

## Current Issues

1. Search results are concatenated into a single text response
2. Metadata is being lost during transmission
3. No clear separation between different matches
4. Limited context for the LLM to understand relevance
5. Difficult to implement proper error handling

## Implementation Plan

### 1. Define New Response Structure

```python
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

@dataclass
class SearchContext:
    before: str  # Content before match
    after: str   # Content after match
    
@dataclass
class SearchMetadata:
    tags: List[str]
    created_at: Optional[datetime]
    modified_at: Optional[datetime]
    path: str
    title: Optional[str]
    relevance_score: float
    
@dataclass
class SearchMatch:
    content: str
    metadata: SearchMetadata
    context: SearchContext

@dataclass    
class SearchResult:
    matches: List[SearchMatch]
    total_matches: int
    query: str
    execution_time: float
```

### 2. Update Server Components

#### 2.1 Indexer.py Updates
- [ ] Replace Dictionary returns with proper dataclasses
- [ ] Implement context window extraction
- [ ] Add metadata enrichment
- [ ] Add relevance scoring
- [ ] Add proper error classes and handling

#### 2.2 Server.py Updates
- [ ] Create Pydantic models for request/response
- [ ] Update query handling to use new structure
- [ ] Implement error type hierarchy
- [ ] Add result validation
- [ ] Add structured logging

### 3. Add Result Processing Features

#### 3.1 Deduplication
- [ ] Implement content-based deduplication
- [ ] Add near-duplicate detection using embeddings
- [ ] Create configurable similarity thresholds
- [ ] Add deduplication logging

#### 3.2 Context Enhancement
- [ ] Implement sliding context window
- [ ] Add source document summarization
- [ ] Create configurable context size
- [ ] Add context truncation handling

#### 3.3 Relevance Scoring
- [ ] Use vector similarity scores from Qdrant
- [ ] Add temporal relevance factors
- [ ] Include metadata-based boosting
- [ ] Create score normalization

### 4. Error Handling Improvements

#### 4.1 Custom Exceptions
```python
class SearchError(Exception):
    """Base class for search-related errors"""
    pass

class InvalidQueryError(SearchError):
    """Raised when query is invalid"""
    pass
    
class ProcessingError(SearchError):
    """Raised when processing results fails"""
    pass
    
class ValidationError(SearchError):
    """Raised when results fail validation"""
    pass
```

#### 4.2 Result Validation
```python
from pydantic import BaseModel, Field

class SearchResultModel(BaseModel):
    matches: List[SearchMatch]
    total_matches: int = Field(ge=0)
    query: str = Field(min_length=1)
    execution_time: float = Field(ge=0)
    
    class Config:
        arbitrary_types_allowed = True
```

### 5. Performance Optimizations

#### 5.1 Result Batching
- [ ] Add pagination support to find() method
- [ ] Implement cursor-based pagination
- [ ] Add batch size configuration
- [ ] Create batch processing optimizations

#### 5.2 Caching
- [ ] Add LRU cache for frequent queries
- [ ] Implement cache invalidation on updates
- [ ] Create cache size management
- [ ] Add cache hit/miss metrics

## MCP Best Practices Alignment

### 1. Clear Message Structure
- Use Python dataclasses and Pydantic models
- Maintain consistent field naming
- Include complete metadata
- Preserve context relationships

### 2. Error Handling
- Use custom exception hierarchy
- Include detailed error messages
- Maintain error context
- Support error recovery

### 3. Resource Efficiency
- Implement proper pagination
- Use appropriate batch sizes
- Manage memory usage
- Handle large result sets

### 4. Security Considerations
- Validate all inputs using Pydantic
- Sanitize output data
- Respect access controls
- Handle sensitive data appropriately

## Testing Plan

### 1. Unit Tests
```python
def test_search_result_structure():
    """Test that search results follow the defined structure"""
    result = indexer.find("test query")
    assert isinstance(result, SearchResult)
    assert all(isinstance(m, SearchMatch) for m in result.matches)
    
def test_metadata_extraction():
    """Test that metadata is properly extracted and formatted"""
    match = indexer.find("test query").matches[0]
    assert isinstance(match.metadata.created_at, datetime)
    assert isinstance(match.metadata.tags, list)
    
def test_error_handling():
    """Test proper error handling"""
    with pytest.raises(InvalidQueryError):
        indexer.find("")
```

### 2. Integration Tests
- [ ] Test end-to-end flow
- [ ] Verify client interactions
- [ ] Test error propagation
- [ ] Validate performance

### 3. Performance Tests
- [ ] Measure response times
- [ ] Test with large datasets
- [ ] Verify memory usage
- [ ] Test concurrent requests

## Success Metrics

1. Response structure correctness
2. Metadata completeness
3. Context relevance
4. Error handling coverage
5. Performance benchmarks
6. Client compatibility

## Timeline

1. Structure Definition: 1 day
2. Server Updates: 2-3 days
3. Processing Features: 3-4 days
4. Error Handling: 2 days
5. Optimizations: 2-3 days
6. Testing: 2-3 days

Total Estimated Time: 2 weeks

## Future Considerations

1. Support for additional metadata types
2. Enhanced context extraction methods
3. Advanced relevance scoring algorithms
4. Improved caching strategies
5. Additional optimization opportunities