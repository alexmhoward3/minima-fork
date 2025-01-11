import os
import logging
import asyncio
from indexer import Indexer
from pydantic import BaseModel
from async_queue import AsyncQueue
from fastapi import FastAPI, APIRouter
from contextlib import asynccontextmanager
from async_loop import index_loop, crawl_loop
from datetime import datetime, timedelta
from typing import Optional, List, Literal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

START_INDEXING = os.environ.get('START_INDEXING', 'false').lower() == 'true'

indexer = Indexer()
async_queue = AsyncQueue()
router = APIRouter()

class Query(BaseModel):
    query: str
    
class Document(BaseModel):
    content: str
    metadata: dict = {}

class DeepSearchQuery(BaseModel):
    query: str
    mode: Literal["summary", "timeline", "topics", "trends"]
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    include_raw: bool = False
    tags: Optional[List[str]] = None

@router.post("/query/deep")
async def deep_search(request: DeepSearchQuery):
    logger.info(f"Received deep search request: {request}")
    try:
        # Get base search results with semantic matching
        logger.info(f"Performing semantic search with query: {request.query}")
        
        # Create variations of the query for better matching
        query_variations = [
            request.query,  # Original query
            f"content about {request.query}",  # Content variation
            f"document mentioning {request.query}",  # Document variation
            f"meeting about {request.query}",  # Meeting variation
            f"notes about {request.query}"  # Notes variation
        ]
        
        # Combine results from all query variations
        all_results = []
        seen_ids = set()
        
        for query in query_variations:
            result = indexer.find(query)
            if "output" in result:
                for item in result["output"]:
                    # Use content hash as ID to deduplicate
                    content_hash = hash(item["content"])
                    if content_hash not in seen_ids:
                        seen_ids.add(content_hash)
                        all_results.append(item)
        
        # Combine into single result
        result = {
            "output": all_results,
            "metadata": [r["metadata"] for r in all_results],
            "relevance_scores": [r["metadata"].get("relevance_score", 0) for r in all_results]
        }
        
        logger.info(f"Combined search returned {len(all_results)} unique results")

        # Log the structure of the result for debugging
        logger.debug(f"Result keys: {result.keys() if isinstance(result, dict) else 'Not a dict'}")
        
        if "error" in result:
            logger.error(f"Base search error: {result['error']}")
            return result
            
        # Validate and log result structure
        if not isinstance(result, dict):
            logger.error(f"Expected dict result, got {type(result)}")
            return {"error": "Invalid result format from search"}
            
        # Check required keys
        required_keys = ['output', 'metadata', 'relevance_scores']
        missing_keys = [key for key in required_keys if key not in result]
        if missing_keys:
            logger.error(f"Missing required keys in result: {missing_keys}")
            return {"error": f"Missing required data: {', '.join(missing_keys)}"}
            
        # Log exact structure of first result if any
        if result.get('output') and len(result['output']) > 0:
            logger.info("First result structure:")
            logger.info(f"Keys in result: {result.keys()}")
            logger.info(f"Keys in first output item: {result['output'][0].keys()}")
            if 'metadata' in result['output'][0]:
                logger.info(f"Keys in first output metadata: {result['output'][0]['metadata'].keys()}")
                logger.info(f"Modified date from metadata: {result['output'][0]['metadata'].get('modified_at')}")



            # Filter by date range and tags
            filtered_results = []
            
            for item in result["output"]:
                try:
                    modified_at = item["metadata"].get("modified_at")
                    logger.debug(f"Checking document modified at: {modified_at}")
                    
                    if not modified_at:
                        logger.debug("Document has no modified_at date, skipping")
                        continue
                        
                    modified_date = datetime.fromisoformat(modified_at)
                    
                    # Check if document is within date range
                    is_after_start = not request.start_date or modified_date >= request.start_date
                    is_before_end = not request.end_date or modified_date <= request.end_date
                    
                    logger.info(f"Date comparison for document:")
                    logger.info(f"  Document date: {modified_date}")
                    logger.info(f"  Start date: {request.start_date}")
                    logger.info(f"  End date: {request.end_date}")
                    logger.info(f"  After start?: {is_after_start}")
                    logger.info(f"  Before end?: {is_before_end}")
                    
                    if not (is_after_start and is_before_end):
                        logger.info("Document outside date range, skipping")
                        continue
                    
                    # Check tags if specified
                    if request.tags:
                        doc_tags = set(item["metadata"].get("tags", []))
                        logger.info(f"Document tags: {doc_tags}")
                        logger.info(f"Required tags: {request.tags}")
                        
                        def normalize_tag(tag):
                            # Strip '#' and whitespace, convert to lowercase
                            return tag.strip('#').strip().lower()
                        
                        def tag_matches(doc_tag, request_tag):
                            # Normalize both tags
                            doc_tag = normalize_tag(doc_tag)
                            request_tag = normalize_tag(request_tag)
                            
                            logger.info(f"Comparing normalized tags - doc: {doc_tag}, request: {request_tag}")
                            
                            # Split hierarchical tags
                            doc_parts = doc_tag.split('/')
                            request_parts = request_tag.split('/')
                            
                            logger.info(f"Split parts - doc: {doc_parts}, request: {request_parts}")
                            
                            # Check if the request tag is a prefix of the document tag
                            # This allows matching parent tags to child tags
                            if len(request_parts) <= len(doc_parts):
                                matches = [rp == dp for rp, dp in zip(request_parts, doc_parts)]
                                logger.info(f"Part matches: {matches}")
                                result = all(matches)
                                logger.info(f"Final match result: {result}")
                                return result
                            logger.info("Request tag longer than doc tag, no match")
                            return False
                        
                        # Check if any request tag matches any document tag
                        if not any(
                            any(tag_matches(doc_tag, req_tag) 
                                for doc_tag in doc_tags)
                            for req_tag in request.tags
                        ):
                            logger.info("Document tags don't match required tags, skipping")
                            continue
                        else:
                            logger.info(f"Document tags match requirements")
                    
                    # If we get here, all filters passed
                    filtered_results.append(item)
                    logger.info("Document passed all filters, adding to results")
                        
                except Exception as e:
                    logger.error(f"Error processing document: {str(e)}")
                    continue
                    
            logger.info(f"Found {len(filtered_results)} documents after filtering")
            result["output"] = filtered_results

        # Generate analysis based on mode
        analysis = ""
        if result["output"]:
            if request.mode == "summary":
                analysis = "Here's a summary of the documents found:\n\n"
                for item in result["output"][:5]:  # Limit to top 5 for summary
                    content_preview = item["content"][:200] + "..." if len(item["content"]) > 200 else item["content"]
                    analysis += f"- {content_preview}\n\n"
                    
            elif request.mode == "timeline":
                sorted_docs = sorted(
                    result["output"], 
                    key=lambda x: x["metadata"].get("modified_at", "")
                )
                analysis = "Timeline of documents:\n\n"
                for item in sorted_docs:
                    modified_at = item["metadata"].get("modified_at", "Unknown date")
                    content_preview = item["content"][:100] + "..." if len(item["content"]) > 100 else item["content"]
                    analysis += f"{modified_at}: {content_preview}\n\n"
                    
            elif request.mode == "topics":
                topics = {}
                for item in result["output"]:
                    for tag in item["metadata"].get("tags", []):
                        if tag not in topics:
                            topics[tag] = []
                        topics[tag].append(item["content"])
                
                analysis = "Topics found in documents:\n\n"
                for topic, contents in topics.items():
                    analysis += f"Topic: {topic}\n"
                    analysis += f"Number of documents: {len(contents)}\n\n"
                    
            elif request.mode == "trends":
                time_periods = {}
                for item in result["output"]:
                    modified_at = item["metadata"].get("modified_at", "")
                    if modified_at:
                        period = modified_at[:7]  # Get year-month
                        if period not in time_periods:
                            time_periods[period] = 0
                        time_periods[period] += 1
                
                analysis = "Trend analysis:\n\n"
                for period, count in sorted(time_periods.items()):
                    analysis += f"{period}: {count} documents\n"

        # Prepare response
        response = {
            "analysis": analysis,
            "metadata": {
                "total_documents": len(result["output"]),
                "date_range": f"{request.start_date} to {request.end_date}" if request.start_date and request.end_date else "all time",
                "tags": request.tags if request.tags else "no tag filter"
            }
        }

        if request.include_raw:
            response["raw_results"] = result["output"]
            
        logger.info(f"Deep search complete. Response: {response}")
        return response

    except Exception as e:
        logger.error(f"Error in deep search: {e}")
        return {"error": str(e)}

@router.post(
    "/query", 
    response_description='Query local data storage',
)
async def query(request: Query):
    logger.info(f"Received query: {request.query}")
    try:
        result = indexer.find(request.query)
        logger.info(f"Found results: {result}")
        return result
    except Exception as e:
        logger.error(f"Error in processing query: {e}")
        return {"error": str(e)}
    
@router.post(
    "/embedding", 
    response_description='Get embedding for a query',
)
async def embedding(request: Query):
    logger.info(f"Received embedding request: {request}")
    try:
        result = indexer.embed(request.query)
        logger.info(f"Found {len(result)} results for query: {request.query}")
        return {"result": result}
    except Exception as e:
        logger.error(f"Error in processing embedding: {e}")
        return {"error": str(e)}    

@router.post(
    "/verify-uuid",
    response_description='Check if a document exists by content-based UUID'
)
async def verify_uuid(doc: Document):
    from langchain.docstore.document import Document as LangchainDocument
    
    # Convert to Langchain document
    document = LangchainDocument(
        page_content=doc.content,
        metadata=doc.metadata
    )
    
    try:
        result = indexer.verify_document_uuid(document)
        logger.info(f"UUID verification result: {result}")
        return {"result": result}
    except Exception as e:
        logger.error(f"Error in UUID verification: {e}")
        return {"error": str(e)}

@asynccontextmanager
async def lifespan(app: FastAPI):
    tasks = []
    logger.info(f"Start indexing: {START_INDEXING}")
    try:
        if START_INDEXING:
            tasks.extend([
                asyncio.create_task(crawl_loop(async_queue)),
                asyncio.create_task(index_loop(async_queue, indexer))
            ])
        yield
    finally:
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)


def create_app() -> FastAPI:
    app = FastAPI(
        openapi_url="/indexer/openapi.json",
        docs_url="/indexer/docs",
        lifespan=lifespan
    )
    app.include_router(router)
    return app

app = create_app()