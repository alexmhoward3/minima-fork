import os
import logging
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_mount():
    container_path = "/usr/src/app/local_files"
    logger.info(f"Checking mount at: {container_path}")
    
    if not os.path.exists(container_path):
        logger.error(f"Container path does not exist: {container_path}")
        return
        
    logger.info(f"Container path exists and is accessible")
    
    # List all files in the directory
    try:
        file_count = 0
        for root, dirs, files in os.walk(container_path):
            logger.info(f"\nDirectory: {root}")
            logger.info(f"Subdirectories: {dirs}")
            logger.info(f"Files: {files}")
            file_count += len(files)
        logger.info(f"\nTotal files found: {file_count}")
        
    except Exception as e:
        logger.error(f"Error walking directory: {e}")
        
if __name__ == "__main__":
    check_mount()