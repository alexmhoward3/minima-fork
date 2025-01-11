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

class Query(BaseModel):
    text: Annotated[
        str, 
        Field(description="context to find")
    ]

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
    if "error" in output:
        logging.error(output["error"])
        raise McpError(INTERNAL_ERROR, output["error"])
    
    logging.info(f"Get prompt: {output}")
    if not output.get("results"):
        return [TextContent(type="text", text="No results found.")]
    
    # Format results while preserving full context
    formatted_results = []
    for result in output["results"]:
        for i, item in enumerate(result["output"]):
            score = result["relevance_scores"][i]
            metadata = result["metadata"][i]
            
            result_text = [
                f"\nResult {i+1} (Relevance: {score:.2f}):",
                item["content"]  # Use full content without splitting
            ]
            
            if metadata.get("tags"):
                result_text.append(f"Tags: {', '.join(metadata['tags'])}")
            if metadata.get("modified_at"):
                result_text.append(f"Last modified: {metadata['modified_at']}")
            
            formatted_results.append("\n".join(result_text))
    
    return [TextContent(type="text", text="\n".join(formatted_results))]
    
@server.get_prompt()
async def get_prompt(name: str, arguments: dict | None) -> GetPromptResult:
    if not arguments or "context" not in arguments:
        logging.error("Context is required")
        raise McpError(INVALID_PARAMS, "Context is required")
        
    context = arguments["text"]

    output = await request_data(context)
    if "error" in output:
        error = output["error"]
        logging.error(error)
        return GetPromptResult(
            description=f"Failed to find content for {context}",
            messages=[
                PromptMessage(
                    role="user", 
                    content=TextContent(type="text", text=error),
                )
            ]
        )

    logging.info(f"Get prompt: {output}")
    if not output.get("results"):
        return GetPromptResult(
            description=f"No results found for {context}",
            messages=[
                PromptMessage(
                    role="user",
                    content=TextContent(type="text", text="No results found.")
                )
            ]
        )
    
    # Format results while preserving full context
    formatted_results = []
    for result in output["results"]:
        for i, item in enumerate(result["output"]):
            score = result["relevance_scores"][i]
            metadata = result["metadata"][i]
            
            result_text = [
                f"\nResult {i+1} (Relevance: {score:.2f}):",
                item["content"]  # Use full content without splitting
            ]
            
            if metadata.get("tags"):
                result_text.append(f"Tags: {', '.join(metadata['tags'])}")
            if metadata.get("modified_at"):
                result_text.append(f"Last modified: {metadata['modified_at']}")
            
            formatted_results.append("\n".join(result_text))
    
    return GetPromptResult(
        description=f"Found {len(formatted_results)} results for {context}",
        messages=[
            PromptMessage(
                role="user",
                content=TextContent(type="text", text="\n".join(formatted_results))
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