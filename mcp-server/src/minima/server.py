import logging
import mcp.server.stdio
from typing import Annotated, List
from datetime import datetime
from mcp.server import Server
from pydantic import BaseModel, Field
from mcp.server.stdio import stdio_server
from mcp.shared.exceptions import McpError
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
from mcp.types import (
    GetPromptResult,
    Prompt,
    PromptArgument,
    PromptMessage,
    TextContent,
    Tool,
    INVALID_PARAMS,
    INTERNAL_ERROR,
)

from .search_service import SearchService
from .models import Query, SearchResult, SearchMatch, SearchMetadata, SearchContext
from .exceptions import SearchError, InvalidQueryError, ProcessingError, ValidationError

logging.basicConfig(
    level=logging.DEBUG, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)

server = Server("minima")

from .config import config

# Initialize search service
search_service = SearchService(
    collection_name=config.qdrant.collection_name,
    qdrant_host=config.qdrant.host,
    qdrant_port=config.qdrant.port
)

def validate_search_result(result: SearchResult) -> None:
    """Validate search result structure and content"""
    if not result.matches:
        raise ValidationError("No matches found in result")
    
    for match in result.matches:
        if not match.content:
            raise ValidationError("Empty content in match")
        if not match.metadata:
            raise ValidationError("Missing metadata in match")
        if not match.context:
            raise ValidationError("Missing context in match")

@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="query",
            description="Find a context in local files (PDF, CSV, DOCX, MD, TXT)",
            inputSchema=Query.model_json_schema(),
        )
    ]
    
@server.list_prompts()
async def list_prompts() -> list[Prompt]:
    logging.info("List of prompts")
    return [
        Prompt(
            name="query",
            description="Find a context in a local files",
            arguments=[
                PromptArgument(
                    name="context", description="Context to search", required=True
                )
            ]
        )            
    ]
    
@server.call_tool()
async def call_tool(name, arguments: dict) -> list[TextContent]:
    if name != "query":
        logging.error(f"Unknown tool: {name}")
        raise ValueError(f"Unknown tool: {name}")

    logging.info("Calling tools")
    try:
        args = Query(**arguments)
    except ValueError as e:
        logging.error(str(e))
        raise McpError(INVALID_PARAMS, str(e))
        
    context = args.text
    logging.info(f"Context: {context}")
    if not context:
        logging.error("Context is required")
        raise McpError(INVALID_PARAMS, "Context is required")

    try:
        search_result = await search_service.search(context)
        validate_search_result(search_result)
        
        # Convert to output string
        output = '. '.join(match.content for match in search_result.matches)
        result = []
        result.append(TextContent(type="text", text=output))
        return result
        
    except SearchError as e:
        logging.error(f"Search error: {str(e)}")
        raise McpError(INTERNAL_ERROR, str(e))
    except ValidationError as e:
        logging.error(f"Validation error: {str(e)}")
        raise McpError(INTERNAL_ERROR, str(e))
    
@server.get_prompt()
async def get_prompt(name: str, arguments: dict | None) -> GetPromptResult:
    if not arguments or "context" not in arguments:
        logging.error("Context is required")
        raise McpError(INVALID_PARAMS, "Context is required")
        
    context = arguments["text"]
    
    try:
        search_result = await search_service.search(context)
        validate_search_result(search_result)
        
        # Convert to output string
        output = '. '.join(match.content for match in search_result.matches)
        return GetPromptResult(
            description=f"Found content for this {context}",
            messages=[
                PromptMessage(
                    role="user", 
                    content=TextContent(type="text", text=output)
                )
            ]
        )
        
    except SearchError as e:
        logging.error(f"Search error: {str(e)}")
        return GetPromptResult(
            description=f"Failed to find content for {context}",
            messages=[
                PromptMessage(
                    role="user", 
                    content=TextContent(type="text", text=str(e)),
                )
            ]
        )
    except ValidationError as e:
        logging.error(f"Validation error: {str(e)}")
        return GetPromptResult(
            description=f"Failed to validate search results for {context}",
            messages=[
                PromptMessage(
                    role="user", 
                    content=TextContent(type="text", text=str(e)),
                )
            ]
        )

async def main():
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="minima",
                server_version="0.0.1",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )