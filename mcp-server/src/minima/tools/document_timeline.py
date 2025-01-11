import logging
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum
from mcp.types import Tool, TextContent

from ..models import BaseDocumentQuery, SearchMode, DeepSearchQuery
from ..requestor import request_deep_search

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TimelineInterval(str, Enum):
    DAY = "day"
    WEEK = "week"
    MONTH = "month"

class DocumentTimelineQuery(BaseDocumentQuery):
    group_by: TimelineInterval = Field(
        default=TimelineInterval.DAY,
        description="Timeline grouping interval (day, week, or month)"
    )
    
    @classmethod
    def validate_arguments(cls, arguments: dict) -> dict:
        """Validate and prepare arguments with defaults"""
        if 'group_by' not in arguments:
            arguments['group_by'] = TimelineInterval.DAY
        return arguments

def get_tool() -> Tool:
    """Returns the document timeline tool definition"""
    return Tool(
        name="document_timeline",
        description="""Create a chronological view of notes with key concepts highlighted.
        
        Features:
        - Chronological organization of notes
        - Grouping by day/week/month
        - Optional filtering by tags and date range
        - Key concept highlighting
        - Search query integration
        
        Examples:
        - Show evolution of a topic over time
        - Track development of ideas chronologically
        - View temporal patterns in note-taking
        """,
        inputSchema=DocumentTimelineQuery.model_json_schema()
    )

async def handle_request(arguments: dict) -> List[TextContent]:
    """Handle a document timeline request"""
    try:
        # Parse and validate the query
        validated_args = DocumentTimelineQuery.validate_arguments(arguments)
        query = DocumentTimelineQuery(**validated_args)
        
        # Convert to deep search format
        output = await request_deep_search(DeepSearchQuery(
            query=query.query,
            mode=SearchMode.TIMELINE,
            start_date=query.start_date,
            end_date=query.end_date,
            tags=query.tags,
            include_raw=True  # We need raw content for timeline processing
        ))
        
        if not output or "error" in output:
            error_msg = output.get("error", "Timeline generation failed") if output else "No results"
            return [TextContent(
                type="text",
                text=f"Timeline error: {error_msg}"
            )]

        # Format timeline response
        formatted_response = []
        
        # Add analysis if available
        if output.get("analysis"):
            formatted_response.append(output["analysis"])
            formatted_response.append("")  # Add spacing
            
        # Add timeline data
        if output.get("raw_results"):
            formatted_response.append(f"Timeline (grouped by {query.group_by.value}):")
            
            # Sort results by date
            sorted_results = sorted(
                output["raw_results"],
                key=lambda x: x.get("modified_at", ""),
                reverse=True
            )
            
            # Group and format results based on interval
            current_group = None
            for result in sorted_results:
                date_str = result.get("modified_at", "")
                if not date_str:
                    continue
                    
                try:
                    date = datetime.fromisoformat(date_str)
                    
                    # Format group header based on interval
                    if query.group_by == TimelineInterval.DAY:
                        group = date.strftime("%Y-%m-%d")
                    elif query.group_by == TimelineInterval.WEEK:
                        group = f"Week of {date.strftime('%Y-%m-%d')}"
                    else:  # MONTH
                        group = date.strftime("%B %Y")
                        
                    # Add group header if changed
                    if group != current_group:
                        current_group = group
                        formatted_response.append(f"\n{group}:")
                    
                    # Add entry details
                    formatted_response.append(f"- {result['source']}")
                    if result.get("tags"):
                        formatted_response.append(f"  Tags: {', '.join(result['tags'])}")
                    
                    # Add snippet of content
                    content = result.get("content", "").strip()
                    if content:
                        snippet = content[:200] + "..." if len(content) > 200 else content
                        formatted_response.append(f"  {snippet}")
                        
                except ValueError as e:
                    logger.error(f"Error parsing date {date_str}: {e}")
                    continue
                    
        # Add metadata if available
        if output.get("metadata"):
            formatted_response.append("\nMetadata:")
            for key, value in output["metadata"].items():
                formatted_response.append(f"{key}: {value}")

        return [TextContent(
            type="text",
            text="\n".join(formatted_response)
        )]
        
    except Exception as e:
        logger.exception("Timeline generation failed")
        return [TextContent(
            type="text",
            text=f"Failed to generate timeline: {str(e)}"
        )]