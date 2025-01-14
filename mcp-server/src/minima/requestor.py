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

def get_env_with_default(key: str, default: str = None) -> str:
    """Get environment variable with default value and logging."""
    value = os.environ.get(key, default)
    if value is None:
        if key in ['LOCAL_FILES_PATH', 'CONTAINER_PATH']:
            value = '/usr/src/app/local_files'
            logger.info(f"Using default container path for {key}: {value}")
        elif key == 'HOST_FILES_PATH':
            # Try to get it from LOCAL_FILES_PATH
            value = os.environ.get('LOCAL_FILES_PATH', default)
            if value:
                logger.info(f"Using LOCAL_FILES_PATH for HOST_FILES_PATH: {value}")
        else:
            logger.debug(f"Environment variable {key} not set, using default: {default}")
    else:
        logger.debug(f"Environment variable {key} = {value}")
    return value

def validate_config() -> Dict[str, Any]:
    """Validate required environment variables and paths."""
    config = {
        "LOCAL_FILES_PATH": get_env_with_default("LOCAL_FILES_PATH", "/usr/src/app/local_files"),
        "HOST_FILES_PATH": get_env_with_default("HOST_FILES_PATH"),
        "CONTAINER_PATH": get_env_with_default("CONTAINER_PATH", "/usr/src/app/local_files"),
        "EMBEDDING_MODEL_ID": get_env_with_default("EMBEDDING_MODEL_ID"),
        "EMBEDDING_SIZE": get_env_with_default("EMBEDDING_SIZE"),
        "START_INDEXING": get_env_with_default("START_INDEXING")
    }
    
    status = {
        "valid": True,
        "missing_vars": [],
        "path_status": {},
        "warnings": []
    }
    
    # Check paths
    for path_key in ["LOCAL_FILES_PATH", "CONTAINER_PATH"]:
        path = config[path_key]
        if path:
            exists = os.path.exists(path)
            status["path_status"][path_key] = {
                "path": path,
                "exists": exists
            }
            if not exists:
                status["warnings"].append(f"{path_key} path does not exist: {path}")
    
    # For HOST_FILES_PATH, we don't check existence as it's the path on the host machine
    if config["HOST_FILES_PATH"]:
        status["path_status"]["HOST_FILES_PATH"] = {
            "path": config["HOST_FILES_PATH"],
            "exists": "unknown"  # Can't check host path from container
        }
    
    # Check required variables
    for key, value in config.items():
        if value is None:
            status["missing_vars"].append(key)
            if key not in ["HOST_FILES_PATH"]:  # HOST_FILES_PATH is optional
                status["valid"] = False
    
    if not status["valid"]:
        logger.error(f"Configuration validation failed: {status}")
    else:
        logger.info("Configuration validation passed")
    
    return status

def get_effective_path() -> str:
    """Get the effective file path based on environment configuration."""
    container_path = get_env_with_default("CONTAINER_PATH", "/usr/src/app/local_files")
    local_path = get_env_with_default("LOCAL_FILES_PATH")
    
    # Try container path first
    if os.path.exists(container_path):
        logger.info(f"Using container path: {container_path}")
        return container_path
    
    # Then try local path
    if local_path and os.path.exists(local_path):
        logger.info(f"Using local path: {local_path}")
        return local_path
    
    # Fallback to container path
    logger.warning(f"No valid paths found, falling back to container path: {container_path}")
    return container_path

def translate_path(file_path: str, direction: str = "to_host") -> str:
    """Translate paths between host and container environments."""
    container_path = get_env_with_default("CONTAINER_PATH", "/usr/src/app/local_files")
    host_path = get_env_with_default("HOST_FILES_PATH")
    
    if not host_path:
        return file_path
    
    if direction == "to_host":
        if file_path.startswith(container_path):
            translated = file_path.replace(container_path, host_path)
            logger.debug(f"Translated container path {file_path} to host path {translated}")
            return translated
    else:  # to_container
        if file_path.startswith(host_path):
            translated = file_path.replace(host_path, container_path)
            logger.debug(f"Translated host path {file_path} to container path {translated}")
            return translated
    
    return file_path

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
                if isinstance(data["output"], list):
                    for item in data["output"]:
                        if "metadata" in item and "file_path" in item["metadata"]:
                            item["metadata"]["file_path"] = translate_path(
                                item["metadata"]["file_path"], 
                                "to_host"
                            )
                
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
        logger.info(f"Using effective path: {effective_path}")

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
                        file_path = metadata.get('file_path', 'Unknown')
                        
                        if file_path != 'Unknown':
                            file_path = translate_path(file_path, "to_host")
                        
                        processed_result = {
                            "source": file_path,
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