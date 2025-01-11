from datetime import datetime
from typing import Optional, List
from pydantic import Field
from mcp.types import Tool, TextContent

from ..models import BaseDocumentQuery, SearchMode, DeepSearchQuery
from ..requestor import request_deep_search
import logging

class DocumentSummaryQuery(BaseDocumentQuery):
    """Document summary specific query parameters"""

def get_tool() -> Tool:
    """Return the document_summary tool definition"""
    return Tool(
        name="document_summary",
        description="""Summarize and analyze notes based on search criteria.
        
        Examples:
        - Summarize all my notes about machine learning from the last 3 months
        - Give me an overview of notes tagged with #book-notes
        - Find and summarize everything I've written about personal knowledge management
        """,
        inputSchema=DocumentSummaryQuery.model_json_schema()
    )

async def handle_request(arguments: dict) -> list[TextContent]:
    """Handle a document_summary tool request"""
    try:
        args = DocumentSummaryQuery(**arguments)
        logging.info(f"Document summary args: {args.dict()}")
        
        output = await request_deep_search(DeepSearchQuery(
            query=args.query,
            mode=SearchMode.SUMMARY,
            start_date=args.start_date,
            end_date=args.end_date,
            tags=args.tags,
            include_raw=args.include_raw
        ))
        
        if not output or "error" in output:
            error_msg = output.get("error", "Search failed") if output else "No results"
            return [TextContent(
                type="text",
                text=f"Search failed: {error_msg}"
            )]
            
        # Format response
        formatted_response = []
        
        # Add total documents count
        total_docs = len(output.get("raw_results", [])) if "raw_results" in output else 0
        formatted_response.append(f"Total documents: {total_docs}")
        
        if output.get("analysis"):
            formatted_response.append(output["analysis"])
        
        if args.include_raw and output.get("raw_results"):
            formatted_response.append("\nDetailed Results:")
            for i, result in enumerate(output["raw_results"], 1):
                formatted_response.append(f"\nDocument {i}:")
                formatted_response.append(f"Source: {result.get('source', 'Unknown')}")
                formatted_response.append(result.get('content', 'No content'))
                
                tags = result.get('metadata', {}).get('tags', [])
                if tags:
                    formatted_response.append(f"Tags: {', '.join(tags)}")
                    
                modified = result.get('metadata', {}).get('modified_at')
                if modified:
                    formatted_response.append(f"Last modified: {modified}")
        
        return [TextContent(
            type="text", 
            text="\n".join(formatted_response)
        )]
        
    except Exception as e:
        logging.exception("Document summary failed")
        return [TextContent(
            type="text",
            text=f"Summary failed: {str(e)}"
        )]