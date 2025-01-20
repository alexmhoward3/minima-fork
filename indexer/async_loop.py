import os
import uuid
import asyncio
import logging
from indexer import Indexer
from ignore_patterns import IgnorePatterns
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)
executor = ThreadPoolExecutor()

CONTAINER_PATH = os.environ.get("CONTAINER_PATH", "/usr/src/app/local_files")
AVAILABLE_EXTENSIONS = [".pdf", ".xls", "xlsx", ".doc", ".docx", ".txt", ".md", ".csv", ".ppt", ".pptx"]

# Initialize ignore patterns
ignore_patterns = None

def init_ignore_patterns():
    global ignore_patterns
    if ignore_patterns is None:
        logger.info(f"Initializing ignore patterns with container path: {CONTAINER_PATH}")
        ignore_patterns = IgnorePatterns(CONTAINER_PATH)

async def crawl_loop(async_queue):
    logger.info(f"Starting crawl loop with path: {CONTAINER_PATH}")
    
    # Initialize ignore patterns
    init_ignore_patterns()
    
    existing_file_paths: list[str] = []
    
    for root, dirs, files in os.walk(CONTAINER_PATH):
        logger.info(f"Processing folder: {root}")
        
        # Skip entire directories that should be ignored
        dirs[:] = [d for d in dirs if not ignore_patterns.should_ignore(os.path.join(root, d))]
        
        for file in files:
            # Skip .minimaignore itself
            if file == '.minimaignore':
                continue
                
            path = os.path.join(root, file)
            
            # Check if file should be ignored
            if ignore_patterns.should_ignore(path):
                logger.info(f"Skipping ignored file: {path}")
                continue
            
            # Check file extension
            if not any(file.endswith(ext) for ext in AVAILABLE_EXTENSIONS):
                logger.info(f"Skipping file due to extension: {file}")
                continue
                
            message = {
                "path": path,
                "file_id": str(uuid.uuid4()),
                "last_updated_seconds": round(os.path.getmtime(path)),
                "type": "file"
            }
            existing_file_paths.append(path)
            async_queue.enqueue(message)
            logger.info(f"File enqueued: {path}")
            
    aggregate_message = {
        "existing_file_paths": existing_file_paths,
        "type": "all_files"
    }
    async_queue.enqueue(aggregate_message)
    async_queue.enqueue({"type": "stop"})


async def index_loop(async_queue, indexer: Indexer):
    loop = asyncio.get_running_loop()
    logger.info("Starting index loop")
    while True:
        if async_queue.size() == 0:
            logger.info("No files to index. Indexing stopped, all files indexed.")
            await asyncio.sleep(1)
            continue
        message = await async_queue.dequeue()
        logger.info(f"Processing message: {message}")
        try:
            if message["type"] == "file":
                await loop.run_in_executor(executor, indexer.index, message)
            elif message["type"] == "all_files":
                await loop.run_in_executor(executor, indexer.purge, message)
            elif message["type"] == "stop":
                break
        except Exception as e:
            logger.error(f"Error in processing message: {e}")
            logger.error(f"Failed to process message: {message}")
        await asyncio.sleep(1)