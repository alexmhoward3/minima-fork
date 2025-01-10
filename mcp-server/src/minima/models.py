from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime

class SearchContext(BaseModel):
    before: str = Field(description="Content before match")
    after: str = Field(description="Content after match")
    
class SearchMetadata(BaseModel):
    tags: List[str] = Field(default_factory=list)
    created_at: Optional[datetime] = None
    modified_at: Optional[datetime] = None
    path: str
    title: Optional[str] = None
    relevance_score: float = Field(ge=0.0, le=1.0)
    
class SearchMatch(BaseModel):
    content: str
    metadata: SearchMetadata
    context: SearchContext
    
class SearchResult(BaseModel):
    matches: List[SearchMatch]
    total_matches: int = Field(ge=0)
    query: str = Field(min_length=1)
    execution_time: float = Field(ge=0)
    
class Query(BaseModel):
    text: str = Field(min_length=1, description="Context to find")
    
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