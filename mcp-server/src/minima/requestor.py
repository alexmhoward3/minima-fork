import httpx
import logging
from typing import Any, Dict


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

REQUEST_DATA_URL = "http://localhost:8001/query"
DEEP_SEARCH_URL = f"{REQUEST_DATA_URL}/deep"  # Deep search endpoint
REQUEST_HEADERS = {
    'Accept': 'application/json',
    'Content-Type': 'application/json'
}

async def request_data(query):
    payload = {
        "query": query
    }
    async with httpx.AsyncClient() as client:
        try:
            logger.info(f"Requesting data from indexer with query: {query}")
            response = await client.post(REQUEST_DATA_URL, 
                                      headers=REQUEST_HEADERS, 
                                      json=payload)
            response.raise_for_status()
            data = response.json()
            logger.info(f"Received data: {data}")
            
            # Format the results nicely
            results = []
            if "output" in data:
                results.append({
                    "output": data["output"],  # Now contains the full array of results
                    "links": list(data["links"]) if "links" in data else [],
                    "metadata": data.get("metadata", []),
                    "relevance_scores": data.get("relevance_scores", [])
                })
            
            return {
                "results": results,
                "total_results": len(results[0]["metadata"]) if results else 0
            }

        except Exception as e:
            logger.error(f"HTTP error: {e}")
            return { "error": str(e) }

async def request_deep_search(query):
    """
    Handle deep search requests with advanced filtering and analysis capabilities.
    
    Args:
        query: DeepSearchQuery object containing search parameters
    """
    payload = {
        "query": query.query,
        "mode": query.mode,
        "time_frame": query.time_frame,
        "start_date": query.start_date.isoformat() if query.start_date else None,
        "end_date": query.end_date.isoformat() if query.end_date else None,
        "include_raw": query.include_raw,
        "tags": query.tags
    }
    
    # Remove None values from payload
    payload = {k: v for k, v in payload.items() if v is not None}
    
    async with httpx.AsyncClient() as client:
        try:
            logger.info(f"Requesting deep search with parameters: {payload}")
            response = await client.post(
                DEEP_SEARCH_URL,
                headers=REQUEST_HEADERS,
                json=payload,
                timeout=30.0  # Add timeout
            )
            response.raise_for_status()
            data = response.json()
            logger.info(f"Received deep search data: {data}")
            
            # Process the response based on the search mode
            processed_data = {
                "analysis": data.get("analysis"),
                "metadata": data.get("metadata", {})
            }
            
            if query.include_raw:
                processed_data["raw_results"] = []
                for result in data.get("raw_results", []):
                    processed_result = {
                        "source": result.get("source", "Unknown source"),
                        "content": result.get("content", ""),
                        "tags": result.get("tags", []),
                        "modified_at": result.get("modified_at")
                    }
                    processed_data["raw_results"].append(processed_result)
            
            processed_data["total_results"] = len(data.get("raw_results", [])) if data.get("raw_results") else 0
            
            return processed_data

        except Exception as e:
            logger.error(f"Deep search error: {e}")
            return {"error": str(e)}