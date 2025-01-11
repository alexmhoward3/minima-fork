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
    try:
        # Validate mode
        valid_modes = ["summary", "timeline", "topics", "trends"]
        mode = query.mode.value if hasattr(query.mode, 'value') else query.mode
        if mode not in valid_modes:
            logger.error(f"Invalid mode: {mode}")
            return {"error": f"Invalid mode. Must be one of: {', '.join(valid_modes)}"}

        # Construct payload with explicit validation
        payload = {
            "mode": mode,
        }
        
        # Add query if present
        if query.query:
            payload["query"] = query.query.strip()  # Basic sanitization

        # Handle dates with validation
        try:
            if query.start_date:
                payload["start_date"] = query.start_date.isoformat()
                logger.debug(f"Start date parsed: {payload['start_date']}")
        except Exception as e:
            logger.error(f"Error processing start_date: {e}")
            return {"error": f"Invalid start date format: {e}"}

        try:
            if query.end_date:
                payload["end_date"] = query.end_date.isoformat()
                logger.debug(f"End date parsed: {payload['end_date']}")
        except Exception as e:
            logger.error(f"Error processing end_date: {e}")
            return {"error": f"Invalid end date format: {e}"}

        # Handle boolean flag
        payload["include_raw"] = bool(query.include_raw)

        # Handle tags with validation
        if query.tags:
            if not isinstance(query.tags, list):
                logger.error(f"Invalid tags format: {query.tags}")
                return {"error": "Tags must be a list of strings"}
            payload["tags"] = [str(tag).strip() for tag in query.tags if tag]  # Sanitize and filter empty tags

        # Log the final payload for debugging
        logger.info(f"Final deep search payload: {payload}")

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    DEEP_SEARCH_URL,
                    headers=REQUEST_HEADERS,
                    json=payload,
                    timeout=60.0  # Increased timeout
                )
                response.raise_for_status()
                data = response.json()
                logger.info(f"Deep search response status: {response.status_code}")
                logger.debug(f"Deep search response data: {data}")
                
                # Validate response structure
                if not isinstance(data, dict):
                    logger.error(f"Invalid response format: {data}")
                    return {"error": "Invalid response format from server"}

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

            except httpx.TimeoutException:
                logger.error("Deep search request timed out")
                return {"error": "Request timed out"}
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error: {e.response.status_code} - {e.response.text}")
                return {"error": f"HTTP error: {e.response.status_code}"}
            except httpx.RequestError as e:
                logger.error(f"Request error: {e}")
                return {"error": f"Request failed: {str(e)}"}
            except Exception as e:
                logger.error(f"Unexpected error in HTTP request: {e}")
                return {"error": f"Unexpected error: {str(e)}"}

    except Exception as e:
        logger.error(f"Error preparing deep search request: {e}")
        return {"error": f"Failed to prepare request: {str(e)}"}