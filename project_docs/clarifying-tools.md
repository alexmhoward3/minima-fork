# Deep Search Tools Implementation Plan

## Overview

This document outlines the plan for splitting the Deep Search functionality into separate, focused tools for personal knowledge management in Obsidian notes. The implementation will be rolled out in phases, with each phase delivering testable functionality aimed at enhancing note discovery and analysis.

## Phase 1: Document Summary Tool

### Implementation
```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

class DocumentSummaryQuery(BaseModel):
    query: Optional[str] = Field(
        None, 
        description="Optional semantic search query"
    )
    start_date: Optional[datetime] = Field(
        None,
        description="Start date for filtering"
    )
    end_date: Optional[datetime] = Field(
        None,
        description="End date for filtering"
    )
    tags: Optional[List[str]] = Field(
        None,
        description="Filter by tags"
    )
    include_raw: bool = Field(
        False,
        description="Include raw document contents"
    )

@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="document_summary",
            description="Summarize and analyze notes based on search criteria",
            inputSchema=DocumentSummaryQuery.model_json_schema()
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    if name == "document_summary":
        query = DocumentSummaryQuery(**arguments)
        results = await process_document_summary(query)
        return [types.TextContent(type="text", text=results)]
```

### User Scenarios
1. "Summarize all my notes about machine learning from the last 3 months"
2. "Give me an overview of notes tagged with #book-notes"
3. "Find and summarize everything I've written about personal knowledge management"

### Testing Steps
1. Test basic semantic search without filters
2. Test date range filtering
3. Test tag filtering
4. Test combined filters
5. Verify summary captures key note content
6. Test YAML frontmatter handling

## Phase 2: Document Timeline Tool

### Implementation
```python
from enum import Enum

class TimelineInterval(str, Enum):
    DAY = "day"
    WEEK = "week"
    MONTH = "month"

class DocumentTimelineQuery(BaseModel):
    query: Optional[str] = Field(
        None,
        description="Optional semantic search query"
    )
    start_date: Optional[datetime] = Field(
        None,
        description="Start date for timeline"
    )
    end_date: Optional[datetime] = Field(
        None,
        description="End date for timeline"
    )
    tags: Optional[List[str]] = Field(
        None,
        description="Filter by tags"
    )
    group_by: TimelineInterval = Field(
        TimelineInterval.DAY,
        description="Timeline grouping interval"
    )
    include_raw: bool = Field(
        False,
        description="Include raw document contents"
    )

@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="document_timeline",
            description="Create a chronological view of notes with key concepts highlighted",
            inputSchema=DocumentTimelineQuery.model_json_schema()
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    if name == "document_timeline":
        query = DocumentTimelineQuery(**arguments)
        results = await process_document_timeline(query)
        return [types.TextContent(type="text", text=results)]
```

### User Scenarios
1. "Show me how my understanding of Zettelkasten evolved over time"
2. "Create a timeline of my daily notes from last month"
3. "What's the progression of my learning about quantum computing?"

### Testing Steps
1. Test basic timeline creation
2. Test daily/weekly/monthly grouping
3. Test timeline filtering by tags
4. Verify chronological ordering
5. Check concept highlighting
6. Test modification date handling

## Phase 3: Document Topics Tool

### Implementation
```python
class DocumentTopicsQuery(BaseModel):
    query: Optional[str] = Field(
        None,
        description="Optional semantic search query"
    )
    start_date: Optional[datetime] = Field(
        None,
        description="Start date for filtering"
    )
    end_date: Optional[datetime] = Field(
        None,
        description="End date for filtering"
    )
    tags: Optional[List[str]] = Field(
        None,
        description="Filter by tags"
    )
    min_topic_frequency: int = Field(
        2,
        description="Minimum occurrences for topic inclusion",
        ge=1
    )
    include_raw: bool = Field(
        False,
        description="Include raw document contents"
    )

@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="document_topics",
            description="Extract and group key topics from notes",
            inputSchema=DocumentTopicsQuery.model_json_schema()
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    if name == "document_topics":
        query = DocumentTopicsQuery(**arguments)
        results = await process_document_topics(query)
        return [types.TextContent(type="text", text=results)]
```

### User Scenarios
1. "What are the main themes in my research notes?"
2. "Find common concepts across my literature notes"
3. "Identify key topics in my notes about programming"

### Testing Steps
1. Test topic extraction from notes
2. Test topic grouping by relevance
3. Test topic frequency filtering
4. Test tag-based filtering
5. Check topic relationship mapping
6. Verify YAML frontmatter integration

## Phase 4: Document Trends Tool

### Implementation
```python
class DocumentTrendsQuery(BaseModel):
    query: Optional[str] = Field(
        None,
        description="Optional semantic search query"
    )
    start_date: Optional[datetime] = Field(
        None,
        description="Start date for trend analysis"
    )
    end_date: Optional[datetime] = Field(
        None,
        description="End date for trend analysis"
    )
    tags: Optional[List[str]] = Field(
        None,
        description="Filter by tags"
    )
    trend_interval: TimelineInterval = Field(
        TimelineInterval.WEEK,
        description="Interval for trend analysis"
    )
    include_raw: bool = Field(
        False,
        description="Include raw document contents"
    )

@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="document_trends",
            description="Analyze how topics and concepts evolve across your notes over time",
            inputSchema=DocumentTrendsQuery.model_json_schema()
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    if name == "document_trends":
        query = DocumentTrendsQuery(**arguments)
        results = await process_document_trends(query)
        return [types.TextContent(type="text", text=results)]
```

### User Scenarios
1. "How has my thinking about AI safety evolved in my notes?"
2. "Show me trends in my learning journal over the past year"
3. "Analyze how my note-taking habits have changed over time"

### Testing Steps
1. Test concept evolution tracking
2. Verify interval grouping
3. Test concept relationship changes
4. Verify tag usage trends
5. Check note frequency patterns
6. Test modification patterns

## Shared Infrastructure

### Common Code Components
```python
class BaseDocumentQuery(BaseModel):
    """Base class for all document query tools"""
    query: Optional[str] = Field(None, description="Optional semantic search query")
    start_date: Optional[datetime] = Field(None, description="Start date for filtering")
    end_date: Optional[datetime] = Field(None, description="End date for filtering")
    tags: Optional[List[str]] = Field(None, description="Filter by tags")
    include_raw: bool = Field(False, description="Include raw document contents")

class DocumentSearchResult(BaseModel):
    """Common result format for all document tools"""
    content: str
    metadata: dict
    score: float = Field(ge=0, le=1)
    
async def validate_date_range(start_date: Optional[datetime], end_date: Optional[datetime]):
    """Shared date validation logic"""
    if start_date and end_date and start_date > end_date:
        raise ValueError("start_date must be before end_date")

async def process_tags(tags: Optional[List[str]]) -> List[str]:
    """Shared tag processing logic"""
    if not tags:
        return []
    return [tag.strip().lower() for tag in tags if tag.strip()]
```

### Performance Considerations
- Implement result pagination for large note collections
- Cache frequent search patterns
- Efficient YAML frontmatter parsing
- Smart indexing of note modifications

### Error Handling Guidelines
1. Input validation errors
2. YAML parsing errors
3. Markdown parsing errors
4. Invalid tag format errors
5. Missing note errors
6. Index errors

## Migration Plan

### Stage 1: Parallel Implementation
1. Implement document_summary tool first
2. Test with various note formats
3. Validate with real Obsidian vault

### Stage 2: Beta Testing
1. Add timeline and topics tools
2. Test with power users
3. Gather feedback on results

### Stage 3: Switchover
1. Add trends tool
2. Deprecate old implementation
3. Update documentation

## Success Metrics
- Note discovery efficiency
- Search relevance
- Response times
- Error rates
- User satisfaction
- Index update speed