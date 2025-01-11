from datetime import datetime
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field, validator

class SearchMode(str, Enum):
    SUMMARY = "summary"
    TIMELINE = "timeline"
    TOPICS = "topics"
    TRENDS = "trends"

class BaseDocumentQuery(BaseModel):
    """Common fields for document queries"""
    query: Optional[str] = Field(None, description="Search query")
    start_date: Optional[datetime] = Field(None, description="Start date for filtering")
    end_date: Optional[datetime] = Field(None, description="End date for filtering")
    tags: Optional[List[str]] = Field(None, description="Filter by tags")
    include_raw: bool = Field(False, description="Include raw document contents")

    @validator('tags', pre=True)
    def validate_tags(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            return [v]  # Convert single string to list
        if isinstance(v, list):
            return v
        raise ValueError('tags must be a string or list of strings')

class DeepSearchQuery(BaseDocumentQuery):
    mode: SearchMode = Field(
        default=SearchMode.SUMMARY,
        description="Type of analysis to perform"
    )