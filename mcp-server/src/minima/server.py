import logging
import mcp.server.stdio
from typing import Annotated, List
from datetime import datetime
from mcp.server import Server
from .requestor import request_data
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


logging.basicConfig(
    level=logging.DEBUG, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)

server = Server("minima")

from .models import Query, SearchResult, SearchMatch, SearchMetadata, SearchContext
from .exceptions import SearchError, InvalidQueryError, ProcessingError, ValidationError

def validate_search_result(result: dict) -> None:
    """Validate search result structure and content"""
    if not result.get('matches'):
        raise ValidationError("No matches found in result")
    
    for match in result['matches']:
        if not match.get('content'):
            raise ValidationError("Empty content in match")
        if not match.get('metadata'):
            raise ValidationError("Missing metadata in match")
        if not match.get('context'):
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

    output = await request_data(context)
    validate_search_result(output['result'])
    if "error" in output:
        logging.error(output["error"])
        raise McpError(INTERNAL_ERROR, output["error"])
    
    logging.info(f"Get prompt: {output}")    
    # Convert raw output to SearchResult model
    raw_output = output['result']
    search_result = SearchResult(
        matches=[SearchMatch(
            content=match['content'],
            metadata=SearchMetadata(**match.get('metadata', {})),
            context=SearchContext(
                before=match.get('context', {}).get('before', ''),
                after=match.get('context', {}).get('after', '')
            )
        ) for match in raw_output.get('matches', [])],
        total_matches=len(raw_output.get('matches', [])),
        query=context,
        execution_time=raw_output.get('execution_time', 0.0)
    )
    
    # Convert to output string
    output = '. '.join(match.content for match in search_result.matches) if search_result.matches else ''
    #links = output['result']['links']
    result = []
    result.append(TextContent(type="text", text=output))
    return result
    
@server.get_prompt()
async def get_prompt(name: str, arguments: dict | None) -> GetPromptResult:
    if not arguments or "context" not in arguments:
        logging.error("Context is required")
        raise McpError(INVALID_PARAMS, "Context is required")
        
    context = arguments["text"]

    output = await request_data(context)
    if "error" in output:
        logger.error(f"Search error: {output['error']}")
    
    try:
        validate_search_result(output['result'])
    except ValidationError as e:
        logger.error(f"Validation error: {str(e)}")
        error = output["error"]
        logging.error(error)
        return GetPromptResult(
            description=f"Faild to find a {context}",
            messages=[
                PromptMessage(
                    role="user", 
                    content=TextContent(type="text", text=error),
                )
            ]
        )

    logging.info(f"Get prompt: {output}")    
    # Convert raw output to SearchResult model
    raw_output = output['result']
    search_result = SearchResult(
        matches=[SearchMatch(
            content=match['content'],
            metadata=SearchMetadata(**match.get('metadata', {})),
            context=SearchContext(
                before=match.get('context', {}).get('before', ''),
                after=match.get('context', {}).get('after', '')
            )
        ) for match in raw_output.get('matches', [])],
        total_matches=len(raw_output.get('matches', [])),
        query=context,
        execution_time=raw_output.get('execution_time', 0.0)
    )
    
    # Convert to output string
    output = '. '.join(match.content for match in search_result.matches) if search_result.matches else ''
    return GetPromptResult(
        description=f"Found content for this {context}",
        messages=[
            PromptMessage(
                role="user", 
                content=TextContent(type="text", text=output)
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