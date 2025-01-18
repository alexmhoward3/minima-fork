import os
import uuid
import asyncio
import logging
from logger_config import configure_logging
from indexer import Indexer
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)
aggregate_logger = configure_logging()
executor = ThreadPoolExecutor()

CONTAINER_PATH = "/usr/src/app/local_files/"
AVAILABLE_EXTENSIONS = [ ".pdf", ".xls", ".docx", ".txt", ".md", ".csv" ]

async def crawl_loop(async_queue):
    logger.info(f"🔄 Starting indexing from {CONTAINER_PATH}")
    file_count = 0
    for root, _, files in os.walk(CONTAINER_PATH):
        logger.debug(f"Processing folder: {root}")
        for file in files:
            if not any(file.endswith(ext) for ext in AVAILABLE_EXTENSIONS):
                logger.debug(f"Skipping unsupported file: {file}")
                continue
            path = os.path.join(root, file)
            message = {
                "path": os.path.join(root, file), 
                "file_id": str(uuid.uuid4())
            }
            async_queue.enqueue(message)
            file_count += 1
            logger.debug(f"Enqueued file: {path}")


async def index_loop(async_queue, indexer: Indexer):
    loop = asyncio.get_running_loop()
    logger.info("🔄 Starting indexing process")
    processed_count = 0
    modified_count = 0
    deleted_count = 0
    while True:
        if async_queue.size() == 0:
            if processed_count > 0:
                logger.info(f"✅ Completed indexing of {processed_count} files ({modified_count} modified, {deleted_count} deleted)")
                processed_count = 0
                modified_count = 0
                deleted_count = 0
            logger.debug("No files in queue")
            await asyncio.sleep(0.1)
            continue
        message = await async_queue.dequeue()
        logger.debug(f"Processing file: {message['path']}")
        processed_count += 1
        try:
            await loop.run_in_executor(executor, indexer.index, message)
        except Exception as e:
            logger.error(f"Error in processing message: {e}")
            logger.error(f"Failed to process message: {message}")

