import httpx
import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

REQUEST_DATA_URL = "http://localhost:8001/query"
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
                    "content": data["output"],
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