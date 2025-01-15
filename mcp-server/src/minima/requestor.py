import os
import httpx
import logging
from typing import Any, Dict, Optional
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

REQUEST_DATA_URL = "http://localhost:8001/query"
DEEP_SEARCH_URL = f"{REQUEST_DATA_URL}/deep"
REQUEST_HEADERS = {
    'Accept': 'application/json',
    'Content-Type': 'application/json'
}

CONTAINER_PATH = "/usr/src/app/local_files"

def get_env_with_default(key: str, default: str = None) -> str:
    """Get environment variable with default value and logging."""
    value = os.environ.get(key, default)
    if value is None:
        logger.debug(f"Environment variable {key} not set, using default: {default}")
    return value

def validate_config() -> Dict[str, Any]:
    """Validate required environment variables."""
    config = {
        "EMBEDDING_MODEL_ID": get_env_with_default("EMBEDDING_MODEL_ID"),
        "EMBEDDING_SIZE": get_env_with_default("EMBEDDING_SIZE"),
        "START_INDEXING": get_env_with_default("START_INDEXING")
    }
    
    status = {
        "valid": True,
        "missing_vars": []
    }
    
    # Check required variables
    for key, value in config.items():
        if value is None:
            status["missing_vars"].append(key)
    
    if not status["valid"]:
        logger.error(f"Configuration validation failed: {status}")
    else:
        logger.info("Configuration validation passed")
    
    return status

def get_effective_path() -> str:
    """Get the container file path."""
    return CONTAINER_PATH

async def request_data(query):
    payload = {"query": query}
    async with httpx.AsyncClient() as client:
        try:
            logger.info(f"Requesting data with query: {query}")
            response = await client.post(REQUEST_DATA_URL, 
                                      headers=REQUEST_HEADERS, 
                                      json=payload)
            response.raise_for_status()
            data = response.json()
            
            results = []
            if "output" in data:
                results.append({
                    "output": data["output"],
                    "links": list(data["links"]) if "links" in data else [],
                    "metadata": data.get("metadata", []),
                    "relevance_scores": data.get("relevance_scores", [])
                })
            
            return {
                "results": results,
                "total_results": len(results[0]["metadata"]) if results else 0
            }

        except Exception as e:
            logger.error(f"Request error: {e}")
            return {"error": str(e)}

async def request_deep_search(query):
    """Handle deep search requests with advanced filtering and analysis."""
    try:
        # Validate configuration
        config_status = validate_config()
        if not config_status["valid"]:
            logger.warning("Some configuration validation failed, continuing with defaults")

        # Get effective path
        effective_path = get_effective_path()
        logger.debug(f"Using path: {effective_path}")

        # Validate mode
        from .models import SearchMode
        mode = query.mode
        if not isinstance(mode, SearchMode):
            logger.error(f"Invalid mode: {mode}")
            return {"error": f"Invalid mode: must be one of {[m.value for m in SearchMode]}"}

        # Build payload
        payload = {
            "mode": mode,
            "query": query.query.strip() if query.query else None,
            "include_raw": bool(query.include_raw)
        }
        
        # Handle dates
        if query.start_date:
            payload["start_date"] = query.start_date.isoformat()
        if query.end_date:
            payload["end_date"] = query.end_date.isoformat()
            
        # Handle tags
        if query.tags:
            if not isinstance(query.tags, list):
                return {"error": "Tags must be a list of strings"}
            payload["tags"] = [str(tag).strip() for tag in query.tags if tag]

        logger.debug(f"Deep search payload: {payload}")

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    DEEP_SEARCH_URL,
                    headers=REQUEST_HEADERS,
                    json=payload,
                    timeout=60.0
                )
                response.raise_for_status()
                data = response.json()
                
                if not isinstance(data, dict):
                    return {"error": "Invalid response format from server"}

                processed_data = {
                    "analysis": data.get("analysis"),
                    "metadata": data.get("metadata", {})
                }
                
                if query.include_raw:
                    processed_data["raw_results"] = []
                    for result in data.get("raw_results", []):
                        metadata = result.get('metadata', {})                        
                        processed_result = {
                            "source": metadata.get('file_path', 'Unknown'),
                            "content": result.get("content", ""),
                            "tags": metadata.get("tags", []),
                            "modified_at": metadata.get("modified_at")
                        }
                        processed_data["raw_results"].append(processed_result)
                
                processed_data["total_results"] = len(data.get("raw_results", [])) if data.get("raw_results") else 0
                
                return processed_data

            except httpx.TimeoutException:
                return {"error": "Request timed out"}
            except httpx.HTTPStatusError as e:
                return {"error": f"HTTP error: {e.response.status_code}"}
            except httpx.RequestError as e:
                return {"error": f"Request failed: {str(e)}"}
            except Exception as e:
                return {"error": f"Unexpected error: {str(e)}"}

    except Exception as e:
        logger.error(f"Error preparing deep search request: {e}")
        return {"error": f"Failed to prepare request: {str(e)}"}
