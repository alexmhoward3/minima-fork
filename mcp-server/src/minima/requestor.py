import logging
import httpx
from typing import Dict, Any

logger = logging.getLogger(__name__)

INDEXER_URL = "http://localhost:8001"  # Make this configurable via environment variable

async def request_data(query: str) -> Dict[str, Any]:
    """Request data from the indexer service"""
    try:
        logger.info(f"Requesting data from indexer with query: {query}")
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{INDEXER_URL}/query",
                json={"query": query},
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()
            logger.debug(f"Received response from indexer: {data}")
            
            # Make sure we have the expected structure
            if "result" not in data:
                logger.warning("Response missing 'result' key")
                data = {"result": {"results": []}}
            
            return data
            
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error when requesting data: {e}")
        return {"error": f"Failed to get data: {str(e)}"}
        
    except httpx.RequestError as e:
        logger.error(f"Request error when requesting data: {e}")
        return {"error": f"Failed to connect to indexer: {str(e)}"}
        
    except Exception as e:
        logger.error(f"Unexpected error when requesting data: {e}")
        return {"error": f"Unexpected error: {str(e)}"}
