import logging
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from mcp.types import Tool, TextContent
from ..requestor import request_data

from .cleanup import CleanupTool  # Import from local module instead

logger = logging.getLogger(__name__)

class Query(BaseModel):
    text: str = Field(description="context to find")

class SearchTool:
    def __init__(self):
        self.name = "query"
        self.description = "Find a context in local files (PDF, CSV, DOCX, MD, TXT)"
    
    def get_tool_definition(self) -> Tool:
        return Tool(
            name=self.name,
            description=self.description,
            inputSchema=Query.model_json_schema(),
        )
    
    async def execute(self, arguments: Dict[str, Any]) -> List[TextContent]:
        try:
            # Validate arguments
            query = Query(**arguments)
            if not query.text:
                raise ValueError("Query text is required")
            
            # Request data from indexer
            logger.debug(f"Executing search with arguments: {arguments}")
            output = await request_data(query.text)
            logger.debug(f"Received output from request_data: {output}")
            
            # Check for errors
            if "error" in output:
                logger.error(f"Error in output: {output['error']}")
                raise ValueError(output["error"])
            
            # Navigate through the content structure to get results
            content = output.get('result', {}).get('content', [])
            results = []
            
            for item in content:
                if item.get('type') == 'application/json':
                    json_content = item.get('json', {})
                    if 'results' in json_content:
                        results = json_content['results']
                        break
            
            logger.debug(f"Extracted results: {results}")
            
            formatted_results = []
            
            for idx, result in enumerate(results, 1):
                try:
                    content = result.get('content', '').strip()
                    metadata = result.get('metadata', {})
                    file_info = metadata.get('file', {})
                    
                    formatted_result = [
                        f"Result {idx}:",
                        f"Source: {file_info.get('url', 'Unknown')}",
                        f"Content: {content}",
                    ]
                    
                    # Add optional metadata
                    if tags := metadata.get('tags'):
                        formatted_result.append(f"Tags: {', '.join(tags)}")
                    
                    if scores := metadata.get('scores'):
                        formatted_result.append(
                            f"Relevance: {scores.get('relevance', 0):.2f}, "
                            f"Similarity: {scores.get('similarity', 0):.2f}"
                        )
                    
                    formatted_result.append("-" * 80)
                    formatted_results.append("\n".join(formatted_result))
                    
                except Exception as e:
                    logger.error(f"Error formatting result {idx}: {e}")
                    continue
            
            # Create final output
            if not formatted_results:
                logger.warning("No results found")
                return [TextContent(type="text", text="No results found.")]
            
            summary = f"Found {len(results)} results for '{query.text}'\n\n"
            combined_output = summary + "\n".join(formatted_results)
            
            logger.debug(f"Final formatted output: {combined_output[:200]}...")
            return [TextContent(type="text", text=combined_output)]
            
        except Exception as e:
            logger.error(f"Search tool execution failed: {e}")
            raise ValueError(f"Search failed: {str(e)}")

class ToolManager:
    def __init__(self):
        self.tools = {
            "query": SearchTool(),
            "cleanup-database": CleanupTool()
        }
    
    def get_tool(self, name: str) -> Any:
        tool = self.tools.get(name)
        if not tool:
            raise ValueError(f"Unknown tool: {name}")
        return tool
    
    def list_tools(self) -> List[Tool]:
        return [tool.get_tool_definition() for tool in self.tools.values()]
    
    async def execute_tool(self, name: str, arguments: Dict[str, Any]) -> List[TextContent]:
        tool = self.get_tool(name)
        return await tool.execute(arguments)