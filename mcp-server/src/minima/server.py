import logging
import mcp.server.stdio
from typing import Annotated
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

from .tools.manager import ToolManager

logger = logging.getLogger(__name__)
server = Server("minima")
tool_manager = ToolManager()

@server.list_tools()
async def list_tools() -> list[Tool]:
    return tool_manager.list_tools()

@server.list_prompts()
async def list_prompts() -> list[Prompt]:
    # We only need one prompt for the query tool
    return [
        Prompt(
            name="query",
            description="Search through local files",
            arguments=[{
                "name": "text",
                "description": "Text to search for",
                "required": True
            }]
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[Tool]:
    try:
        return await tool_manager.execute_tool(name, arguments)
    except ValueError as e:
        raise McpError(INVALID_PARAMS, str(e))
    except Exception as e:
        logger.error(f"Tool execution failed: {e}")
        raise

@server.get_prompt()
async def get_prompt(name: str, arguments: dict | None) -> GetPromptResult:
    if name != "query":
        raise McpError(INVALID_PARAMS, f"Unknown prompt: {name}")
        
    if not arguments or "text" not in arguments:
        raise McpError(INVALID_PARAMS, "Query text is required")
    
    try:
        results = await tool_manager.execute_tool("query", arguments)
        
        if not results:
            return GetPromptResult(
                description=f"No results found for '{arguments['text']}'",
                messages=[
                    PromptMessage(
                        role="user",
                        content=results[0] if results else None
                    )
                ]
            )
            
        return GetPromptResult(
            description=f"Found results for '{arguments['text']}'",
            messages=[
                PromptMessage(
                    role="user",
                    content=results[0]
                )
            ]
        )
        
    except Exception as e:
        logger.error(f"Error getting prompt: {e}")
        raise

async def main():
    """Main entry point for the MCP server"""
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
