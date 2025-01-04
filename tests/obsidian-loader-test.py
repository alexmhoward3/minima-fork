import os
import sys
import asyncio
import logging
from pathlib import Path
import subprocess
import time

# Add parent directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from indexer.indexer import Indexer, Config
from langchain_community.document_loaders import ObsidianLoader

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def ensure_qdrant_running():
    """
    Make sure Qdrant is running, start it if not.
    Returns True if Qdrant is ready to accept connections.
    """
    import requests
    from requests.exceptions import ConnectionError
    
    # Try to connect to Qdrant
    try:
        response = requests.get("http://localhost:6333/collections")
        if response.status_code == 200:
            logger.info("Qdrant is already running")
            return True
    except ConnectionError:
        logger.info("Qdrant is not running, attempting to start via Docker...")
        
        try:
            # Try to start Qdrant via Docker
            subprocess.run(
                ["docker", "run", "-d", "--name", "qdrant_test",
                 "-p", "6333:6333", "-p", "6334:6334",
                 "qdrant/qdrant"],
                check=True
            )
            
            # Wait for Qdrant to be ready
            for _ in range(30):  # Try for 30 seconds
                try:
                    response = requests.get("http://localhost:6333/collections")
                    if response.status_code == 200:
                        logger.info("Qdrant started successfully")
                        return True
                except:
                    time.sleep(1)
                    
            logger.error("Timed out waiting for Qdrant to start")
            return False
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to start Qdrant: {e}")
            return False
    except Exception as e:
        logger.error(f"Error checking Qdrant status: {e}")
        return False

async def test_loaders(test_path: str, test_queries: list[str]):
    """
    Compare TextLoader vs ObsidianLoader using the same test queries
    """
    # Store original environment variables
    original_collection = os.getenv('QDRANT_COLLECTION')
    original_start_indexing = os.getenv('START_INDEXING')
    
    try:
        # Set required environment variables
        os.environ.update({
            'QDRANT_HOST': 'localhost',
            'QDRANT_PORT': '6333',
            'START_INDEXING': 'true',
            'CONTAINER_PATH': test_path,
            'LOCAL_FILES_PATH': test_path,
            'EMBEDDING_MODEL_ID': 'sentence-transformers/all-mpnet-base-v2',
            'EMBEDDING_SIZE': '768'
        })
        
        # Test with ObsidianLoader
        logger.info("Testing with ObsidianLoader...")
        
        loader = ObsidianLoader(test_path)
        documents = loader.load()
        
        # Run test queries
        for query in test_queries:
            logger.info(f"\nTesting query: {query}")
            
            # Get results from ObsidianLoader
            logger.info("\nObsidianLoader Results:")
            for doc in documents:
                logger.info(f"Metadata: {doc.metadata}")
                if query in doc.page_content or (doc.metadata and query in str(doc.metadata)):
                    logger.info(f"Found in document: {doc.metadata['source']}")
                    logger.info(f"First 200 chars: {doc.page_content[:200]}...")
            
    finally:
        # Clean up: restore original environment variables
        if original_collection:
            os.environ['QDRANT_COLLECTION'] = original_collection
        if original_start_indexing:
            os.environ['START_INDEXING'] = original_start_indexing

def main():
    # First ensure Qdrant is running
    if not ensure_qdrant_running():
        logger.error("Could not start Qdrant. Please make sure Docker is running and try again.")
        sys.exit(1)
        
    # Path to test vault
    test_path = os.getenv('LOCAL_FILES_PATH')
    if not test_path:
        logger.error("LOCAL_FILES_PATH environment variable must be set")
        sys.exit(1)
        
    if not os.path.exists(test_path):
        logger.error(f"Test path does not exist: {test_path}")
        sys.exit(1)
        
    logger.info(f"Using test vault at: {test_path}")
        
    # Sample test queries - modify these based on your test vault content
    test_queries = [
        "project architecture",  # General content search
        "#important",           # Tag search
        "[[linked",            # Wikilink search
        "task list",           # Regular search
    ]
    
    # Run tests
    asyncio.run(test_loaders(test_path, test_queries))

if __name__ == "__main__":
    main()
