import logging
import mcp.server.stdio
from typing import Annotated, Optional, List
from pydantic import BaseModel, Field
from mcp.server.stdio import stdio_server
from mcp.shared.exceptions import McpError
from mcp.server import NotificationOptions, Server, InitializationOptions
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

from .models import SearchMode, BaseDocumentQuery
from .requestor import request_data, request_deep_search
from .tools.document_summary import get_tool as get_document_summary_tool, handle_request as handle_document_summary_request

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

class DeepSearchQuery(BaseDocumentQuery):
    mode: SearchMode = Field(
        default=SearchMode.SUMMARY,
        description="Type of analysis to perform"
    )

@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        get_document_summary_tool(),
        Tool(
            name="query",
            description="Find a context in local files (PDF, CSV, DOCX, MD, TXT)",
            inputSchema=Query.model_json_schema(),
        ),
        Tool(
            name="deep_search",
            description="""Advanced semantic search with temporal filtering and analysis capabilities.
            
            Modes:
            - summary: Summarize matching documents
            - timeline: Show documents in chronological order
            - topics: Group documents by tags/topics
            - trends: Analyze document frequency over time
            
            Examples:
            - Find recent meetings about project X
            - Show timeline of documents about Y
            - Analyze trends in discussions about Z
            - Get topics from documents tagged with 'research'
            """,
            inputSchema=DeepSearchQuery.model_json_schema()
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
    if name == "document_summary":
        return await handle_document_summary_request(arguments)
    elif name == "query":
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
        if not output:
            return [TextContent(type="text", text="No results found. Try broadening your search criteria.")]
            
        if "error" in output:
            logging.error(output["error"])
            raise McpError(INTERNAL_ERROR, output["error"])
        
        if not output.get("results"):
            return [TextContent(type="text", text="No results found.")]
        
        # Format results while preserving full context
        formatted_results = []
        for result in output["results"]:
            for i, item in enumerate(result["output"]):
                score = result["relevance_scores"][i]
                metadata = result["metadata"][i]
                
                # Transform the file path to be more readable
                file_path = metadata.get('file_path', 'Unknown path')
                if file_path.startswith('/usr/src/app/local_files/'):
                    file_path = file_path[len('/usr/src/app/local_files/'):]
                
                result_text = [
                    f"\nResult {i+1} (Relevance: {score:.2f}):",
                    f"Source: {file_path}",
                    item["content"]  # Use full content without splitting
                ]
                
                if metadata.get("tags"):
                    result_text.append(f"Tags: {', '.join(metadata['tags'])}")
                if metadata.get("modified_at"):
                    result_text.append(f"Last modified: {metadata['modified_at']}")
                
                formatted_results.append("\n".join(result_text))
        
        return [TextContent(type="text", text="\n".join(formatted_results))]
    
    elif name == "deep_search":
        try:
            args = DeepSearchQuery(**arguments)
            logging.info(f"Deep search args: {args.dict()}")
        except ValueError as e:
            error_msg = str(e)
            if "mode" in error_msg:
                error_msg = "Mode must be one of: summary, timeline, topics, or trends"
            logging.error(f"Validation error: {error_msg}")
            return [TextContent(
                type="text", 
                text=f"Invalid search parameters: {error_msg}"
            )]
            
        try:
            output = await request_deep_search(args)
            
            if not output or "error" in output:
                error_msg = output.get("error", "Search failed") if output else "No results"
                return [TextContent(
                    type="text",
                    text=f"Search error: {error_msg}"
                )]
                
            # Format response
            formatted_response = []
            
            if output.get("analysis"):
                formatted_response.append(f"\nAnalysis ({args.mode}):")
                formatted_response.append(output["analysis"])
            
            if args.include_raw and output.get("raw_results"):
                formatted_response.append("\nRaw Results:")
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
            
            metadata = output.get("metadata", {})
            if metadata:
                formatted_response.append("\nMetadata:")
                for key, value in metadata.items():
                    formatted_response.append(f"{key}: {value}")
            
            return [TextContent(
                type="text", 
                text="\n".join(formatted_response)
            )]
            
        except Exception as e:
            logging.exception("Deep search failed")
            return [TextContent(
                type="text",
                text=f"Search failed: {str(e)}"
            )]
    
    else:
        logging.error(f"Unknown tool: {name}")
        raise ValueError(f"Unknown tool: {name}")

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