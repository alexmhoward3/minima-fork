from datetime import datetime
from enum import Enum
from typing import Optional, List
from pydantic import Field
from mcp.types import Tool, TextContent

from ..models import BaseDocumentQuery, SearchMode, DeepSearchQuery
from ..requestor import request_deep_search
import logging

class TimelineInterval(str, Enum):
    """Time intervals for trend analysis"""
    DAY = "day"
    WEEK = "week"
    MONTH = "month"

class DocumentTrendsQuery(BaseDocumentQuery):
    """Document trends specific query parameters"""
    trend_interval: TimelineInterval = Field(
        default=TimelineInterval.MONTH,
        description="Interval for trend analysis"
    )

def get_tool() -> Tool:
    """Return the document_trends tool definition"""
    return Tool(
        name="document_trends",
        description="""Analyze frequency and content patterns in your notes over time.
        Shows document count trends and provides relevant examples.
        
        Examples:
        - How often have I written about leadership over the past year?
        - Show me the trend of my writing about project management
        - What's the pattern of my notes about machine learning?
        """,
        inputSchema=DocumentTrendsQuery.model_json_schema()
    )

async def handle_request(arguments: dict) -> list[TextContent]:
    """Handle a document_trends tool request"""
    try:
        args = DocumentTrendsQuery(**arguments)
        logging.info(f"Document trends args: {args.dict()}")
        
        output = await request_deep_search(DeepSearchQuery(
            query=args.query,
            mode=SearchMode.TRENDS,
            start_date=args.start_date,
            end_date=args.end_date,
            tags=args.tags,
            include_raw=args.include_raw
        ))
        
        if not output or "error" in output:
            error_msg = output.get("error", "Analysis failed") if output else "No results"
            return [TextContent(
                type="text",
                text=f"Trend analysis failed: {error_msg}"
            )]
            
        # Format response
        formatted_response = []
        
        if output.get("analysis"):
            formatted_response.append(output["analysis"])
            formatted_response.append("")  # Add spacing
        
        if args.include_raw and output.get("raw_results"):
            formatted_response.append("Documents Examples:")
            for i, result in enumerate(output["raw_results"], 1):
                formatted_response.append(f"\nDocument {i}:")
                formatted_response.append(f"Source: {result.get('source', 'Unknown')}")
                formatted_response.append(result.get('content', 'No content'))
                
                # Include metadata if available
                metadata = result.get('metadata', {})
                if metadata.get('tags'):
                    formatted_response.append(f"Tags: {', '.join(metadata['tags'])}")
                if metadata.get('modified_at'):
                    formatted_response.append(f"Last modified: {metadata['modified_at']}")
        
        return [TextContent(
            type="text", 
            text="\n".join(formatted_response)
        )]
        
    except Exception as e:
        logging.exception("Document trends analysis failed")
        return [TextContent(
            type="text",
            text=f"Trend analysis failed: {str(e)}"
        )]