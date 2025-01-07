import logging
from typing import Dict, List
from qdrant_client import QdrantClient
from qdrant_client.http import models

logger = logging.getLogger(__name__)

class QdrantCleanup:
    def __init__(self, client: QdrantClient, collection_name: str):
        self.client = client
        self.collection_name = collection_name

    def quick_duplicate_check(self) -> Dict[str, int]:
        """Do a fast check for potential duplicates"""
        try:
            scroll_result = self.client.scroll(
                collection_name=self.collection_name,
                with_payload=True,
                limit=1000  # Start with first 1000 for speed
            )
            
            points = scroll_result[0]
            paths = {}
            
            for point in points:
                path = self._extract_file_path(point.payload)
                if path:
                    if path not in paths:
                        paths[path] = 0
                    paths[path] += 1
            
            duplicates = {k:v for k,v in paths.items() if v > 1}
            return {
                "total_points": len(points),
                "unique_files": len(paths),
                "files_with_duplicates": len(duplicates),
                "total_duplicates": sum(v-1 for v in duplicates.values())
            }
        except Exception as e:
            logger.error(f"Error during duplicate check: {e}")
            raise

    def _extract_file_path(self, payload: Dict) -> str:
        """Extract file path from payload, checking various possible locations."""
        metadata = payload.get('metadata', {})
        return (metadata.get('file_path') or 
                payload.get('file_path') or 
                metadata.get('source') or 
                payload.get('source'))

    def cleanup_duplicates(self) -> Dict[str, int]:
        """
        Remove duplicate embeddings from the collection.
        Duplicates are identified by file path in payload.
        """
        try:
            logger.info("Starting duplicate cleanup")
            
            # Get all points from the collection
            scroll_result = self.client.scroll(
                collection_name=self.collection_name,
                with_payload=True,
                limit=10000  # Adjust based on collection size
            )
            
            points = scroll_result[0]  # [0] contains points, [1] contains next_page_offset
            
            # Group points by file path
            points_by_file = {}
            for point in points:
                file_path = self._extract_file_path(point.payload)
                if not file_path:
                    continue
                    
                if file_path not in points_by_file:
                    points_by_file[file_path] = []
                points_by_file[file_path].append(point.id)
            
            # Find duplicate groups
            duplicate_ids = self._get_duplicate_ids(points_by_file)
            
            if duplicate_ids:
                logger.info(f"Found {len(duplicate_ids)} duplicate points to remove")
                self._delete_duplicates(duplicate_ids)
            
            logger.info("Duplicate cleanup completed")
            return {
                "total_points": len(points),
                "duplicates_removed": len(duplicate_ids),
                "files_affected": len([k for k,v in points_by_file.items() if len(v) > 1])
            }
            
        except Exception as e:
            logger.error(f"Error during duplicate cleanup: {str(e)}")
            raise

    def _get_duplicate_ids(self, points_by_file: Dict[str, List[str]]) -> List[str]:
        """Get list of IDs for duplicate points, keeping first occurrence of each."""
        duplicate_ids = []
        for file_path, point_ids in points_by_file.items():
            if len(point_ids) > 1:
                # Keep the first occurrence, mark others for deletion
                duplicate_ids.extend(point_ids[1:])
        return duplicate_ids

    def _delete_duplicates(self, duplicate_ids: List[str], batch_size: int = 100):
        """Delete duplicate points in batches."""
        for i in range(0, len(duplicate_ids), batch_size):
            batch = duplicate_ids[i:i + batch_size]
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=models.PointIdsList(
                    points=batch
                )
            )
            logger.info(f"Deleted batch of {len(batch)} duplicates")