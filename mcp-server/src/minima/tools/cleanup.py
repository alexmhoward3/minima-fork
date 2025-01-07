import logging
from typing import Dict, Any
from pydantic import BaseModel
from mcp.types import Tool, TextContent
from indexer.indexer.indexer import Indexer
from indexer.indexer.cleanup import QdrantCleanup

logger = logging.getLogger(__name__)

class CleanupTool:
    def __init__(self):
        self.name = "cleanup-database"
        self.description = "Remove duplicate entries from the vector database"
        self.indexer = Indexer()
        self.cleanup = QdrantCleanup(
            self.indexer.qdrant, 
            self.indexer.config.QDRANT_COLLECTION
        )
    
    def get_tool_definition(self) -> Tool:
        return Tool(
            name=self.name,
            description=self.description,
            inputSchema={
                "type": "object",
                "properties": {}  # No input needed
            }
        )
    
    async def execute(self, arguments: Dict[str, Any]) -> List[TextContent]:
        try:
            # First check for duplicates
            check_results = self.cleanup.quick_duplicate_check()
            
            if check_results["total_duplicates"] == 0:
                return [TextContent(
                    type="text",
                    text="No duplicates found in the database."
                )]
            
            # Run cleanup
            cleanup_results = self.cleanup.cleanup_duplicates()
            
            return [TextContent(
                type="text",
                text=f"Cleanup completed:\n"
                     f"- Removed {cleanup_results['duplicates_removed']} duplicates\n"
                     f"- Affected {cleanup_results['files_affected']} files\n"
                     f"- Total points processed: {cleanup_results['total_points']}"
            )]
            
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
            raise ValueError(f"Cleanup failed: {str(e)}")
