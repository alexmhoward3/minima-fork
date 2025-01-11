from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from mcp.types import Tool, TextContent

from ..models import BaseDocumentQuery, SearchMode, DeepSearchQuery
from ..requestor import request_deep_search

class DocumentTopicsQuery(BaseDocumentQuery):
    """Query parameters for topic extraction from documents"""
    min_topic_frequency: int = Field(
        2,
        description="Minimum occurrences for topic inclusion",
        ge=1
    )

def get_tool() -> Tool:
    """Return the tool definition for document topics analysis"""
    return Tool(
        name="document_topics",
        description="Extract and group key topics from notes. Identifies main themes, concepts, and their relationships across your documents.",
        inputSchema=DocumentTopicsQuery.model_json_schema()
    )

async def handle_request(arguments: dict) -> List[TextContent]:
    """Handle a document topics analysis request"""
    try:
        # Validate and process arguments
        query = DocumentTopicsQuery(**arguments)
        
        # Convert to deep search query
        output = await request_deep_search(DeepSearchQuery(
            query=query.query,
            mode=SearchMode.TOPICS,
            start_date=query.start_date,
            end_date=query.end_date,
            tags=query.tags,
            include_raw=query.include_raw
        ))
        
        if not output or "error" in output:
            error_msg = output.get("error", "Analysis failed") if output else "No results"
            return [TextContent(
                type="text",
                text=f"Topic analysis error: {error_msg}"
            )]
        
        # Format response
        formatted_response = []
        
        if output.get("analysis"):
            formatted_response.append("Topic Analysis Results:")
            formatted_response.append(output["analysis"])
        
        if query.include_raw and output.get("raw_results"):
            formatted_response.append("\nDetailed Document Breakdown:")
            for i, result in enumerate(output["raw_results"], 1):
                formatted_response.append(f"\nDocument {i}:")
                formatted_response.append(f"Source: {result.get('source', 'Unknown')}")
                formatted_response.append(result.get('content', 'No content'))
                
                # Include metadata like tags and modification date
                metadata = result.get('metadata', {})
                if metadata.get('tags'):
                    formatted_response.append(f"Tags: {', '.join(metadata['tags'])}")
                if metadata.get('modified_at'):
                    formatted_response.append(f"Last modified: {metadata['modified_at']}")
                
                # Include topic-specific metadata if available
                if result.get('topics'):
                    formatted_response.append(f"Main topics: {', '.join(result['topics'])}")
        
        # Include summary statistics if available
        metadata = output.get("metadata", {})
        if metadata:
            formatted_response.append("\nAnalysis Statistics:")
            for key, value in metadata.items():
                formatted_response.append(f"{key}: {value}")
        
        return [TextContent(
            type="text",
            text="\n".join(formatted_response)
        )]
        
    except Exception as e:
        return [TextContent(
            type="text",
            text=f"Topic analysis failed: {str(e)}"
        )]