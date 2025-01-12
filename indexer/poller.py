import os
import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Set, Dict, Optional

logger = logging.getLogger(__name__)

class AsyncPollingService:
    def __init__(self, indexer, interval_seconds: int = 300):
        self.indexer = indexer
        self.interval_seconds = interval_seconds
        self.is_running = False
        self._last_check_times: Dict[str, float] = {}  # Cache of last check times
        self._last_mod_times: Dict[str, float] = {}   # Cache of last known modification times
        
    async def start(self):
        """Start the polling service"""
        self.is_running = True
        while self.is_running:
            try:
                await self.poll_for_changes()
                await asyncio.sleep(self.interval_seconds)
            except Exception as e:
                logger.error(f"Error in polling loop: {e}")
                await asyncio.sleep(10)  # Short sleep on error before retry
                
    async def stop(self):
        """Stop the polling service"""
        self.is_running = False
        
    async def poll_for_changes(self):
        """Check for modified files and trigger reindexing"""
        container_path = self.indexer.config.CONTAINER_PATH
        logger.debug(f"Polling for changes in {container_path}")
        
        modified_files = set()
        
        try:
            # Walk through all files in the container path
            for root, _, files in os.walk(container_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    if not any(file.endswith(ext) for ext in self.indexer.config.EXTENSIONS_TO_LOADERS.keys()):
                        continue
                        
                    # Check if file should be ignored
                    if self.indexer._should_ignore(file_path):
                        logger.debug(f"Ignoring file due to .minimaignore: {file_path}")
                        continue
                        
                    try:
                        # Get current file modification time
                        current_mtime = os.path.getmtime(file_path)
                        
                        # Get last known modification time from cache
                        last_known_mtime = self._last_mod_times.get(file_path)
                        
                        # Only check Qdrant if file is new or modified since last check
                        if last_known_mtime is None or current_mtime > last_known_mtime:
                            # Get last indexed time from Qdrant
                            last_indexed = await self.indexer.get_last_indexed_time(file_path)
                            
                            # Check if file needs reindexing
                            if last_indexed is None or current_mtime > last_indexed:
                                logger.info(f"Modified file detected: {file_path}")  # Keeping this as INFO for visibility
                                modified_files.add(file_path)
                        
                        # Update our cache
                        self._last_mod_times[file_path] = current_mtime
                            
                    except Exception as e:
                        logger.error(f"Error checking file {file_path}: {e}")
                        continue
            
            # Process modified files
            if modified_files:
                for file_path in modified_files:
                    try:
                        # Create indexing message
                        message = {
                            "path": file_path,
                            "file_id": str(Path(file_path).stem),
                            "modified_at": datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
                        }
                        
                        # Process the file
                        await self.indexer.index_async(message)
                        logger.debug(f"Successfully reindexed {file_path}")
                        
                    except Exception as e:
                        logger.error(f"Error processing modified file {file_path}: {e}")
                        
        except Exception as e:
            logger.error(f"Error during polling: {e}")
            raise  # Re-raise the exception after logging