import os
import logging
import asyncio
from logger_config import configure_logging
from indexer import Indexer
from pydantic import BaseModel
from async_queue import AsyncQueue
from fastapi import FastAPI, APIRouter
from contextlib import asynccontextmanager
from async_loop import index_loop, crawl_loop
from datetime import datetime, timedelta
from typing import Optional, List, Literal
from enum import Enum

# Configure logging once at startup
aggregate_logger = configure_logging(force=True)
logger = logging.getLogger(__name__)

# Disable noisy logs
logging.getLogger('uvicorn.access').setLevel(logging.WARNING)
logging.getLogger('uvicorn.error').setLevel(logging.WARNING)
logging.getLogger('asyncio').setLevel(logging.WARNING)

raw_start_indexing = os.environ.get('START_INDEXING', 'false')
logger.info(f"Raw START_INDEXING value: {raw_start_indexing}")
START_INDEXING = raw_start_indexing.lower() == 'true'

indexer = Indexer()
async_queue = AsyncQueue()
router = APIRouter()

class SearchMode(str, Enum):
    SUMMARY = "summary"
    TIMELINE = "timeline"
    TOPICS = "topics"
    TRENDS = "trends"

class Query(BaseModel):
    query: str
    
class Document(BaseModel):
    content: str
    metadata: dict = {}

class DeepSearchQuery(BaseModel):
    query: Optional[str] = None
    mode: Literal["summary", "timeline", "topics", "trends"]
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    include_raw: bool = False
    tags: Optional[List[str]] = None

@router.post("/query/deep")
async def deep_search(request: DeepSearchQuery):
    logger.info(f"Received deep search request: {request}")
    try:
        # Validate date range if provided
        if request.start_date and request.end_date:
            if request.end_date < request.start_date:
                raise ValueError("End date must be after start date")
                
            # Ensure dates aren't in the future
            now = datetime.now()
            if request.end_date > now:
                request.end_date = now
                logger.warning("Adjusted end_date to current time")
                
        # Validate tags if provided
        if request.tags:
            clean_tags = []
            for tag in request.tags:
                if isinstance(tag, str):
                    # Strip '#' and whitespace, ensure non-empty
                    cleaned = tag.strip('#').strip()
                    if cleaned:
                        clean_tags.append(cleaned)
            request.tags = clean_tags
            
            if not request.tags:
                logger.warning("All provided tags were invalid or empty")
        
        # Get base search results
        all_results = []
        if request.query:
            # Do semantic search if query is provided
            logger.info(f"Performing semantic search with query: {request.query}")
            
            # Create semantic variations of the query
            query_variations = [
                request.query,  # Original query
                f"content about {request.query}",  # Content variation
                f"document mentioning {request.query}",  # Document variation
                f"meeting about {request.query}",  # Meeting variation
                f"notes about {request.query}",  # Notes variation
                f"information regarding {request.query}",  # Additional variation
                f"discussion of {request.query}"  # Discussion variation
            ]
            
            # Use set for deduplication with content hash
            seen_ids = set()
            
            for query in query_variations:
                try:
                    result = indexer.find(query)
                    if not result or "error" in result or "output" not in result:
                        continue
                        
                    for item in result["output"]:
                        try:
                            # Validate required fields
                            if not item.get("content"):
                                continue
                                
                            # Use content hash for deduplication
                            content_hash = hash(item["content"])
                            if content_hash not in seen_ids:
                                seen_ids.add(content_hash)
                                all_results.append(item)
                        except Exception as e:
                            logger.error(f"Error processing result item: {e}")
                            continue
                            
                except Exception as e:
                    logger.error(f"Error processing query variation '{query}': {e}")
                    continue
                    
            result = {
                "output": all_results,
                "metadata": [r["metadata"] for r in all_results],
                "relevance_scores": [r["metadata"].get("relevance_score", 0) for r in all_results]
            }
        else:
            # Do date-range only search if no query provided
            logger.info(f"Performing date-range search: {request.start_date} to {request.end_date}")
            result = indexer.find_by_date_range(
                start_date=request.start_date,
                end_date=request.end_date
            )
            if "error" not in result:
                all_results = result["output"]
            
        logger.info(f"Search returned {len(result.get('output', [])) if isinstance(result, dict) else 0} results")

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

        if not all_results:
            logger.info("No matching documents found")
            return {
                "analysis": "No documents found matching your criteria.",
                "metadata": {
                    "total_documents": 0,
                    "date_range": f"{request.start_date} to {request.end_date}" if request.start_date and request.end_date else "all time",
                    "tags": request.tags if request.tags else "no tag filter",
                    "query": request.query,
                    "mode": request.mode
                }
            }

        # Process and validate results
        processed_results = []
        
        if "error" in result:
            logger.error(f"Base search error: {result['error']}")
            return result

        for item in result.get("output", []):
            try:
                # Validate required fields
                if not item.get("content") or not item.get("metadata"):
                    continue

                # Process metadata
                metadata = item["metadata"]
                modified_at = metadata.get("modified_at")
                if modified_at:
                    try:
                        modified_date = datetime.fromisoformat(modified_at)
                        # Apply date filtering if specified
                        if request.start_date and modified_date < request.start_date:
                            continue
                        if request.end_date and modified_date > request.end_date:
                            continue
                    except ValueError:
                        logger.warning(f"Invalid date format in metadata: {modified_at}")
                        continue

                # Process tags
                tags = set(metadata.get("tags", []))
                if request.tags:
                    # Check if any requested tag matches
                    if not any(tag in tags for tag in request.tags):
                        continue

                processed_results.append({
                    "content": item["content"],
                    "metadata": {
                        "file_path": metadata.get("file_path", "Unknown"),
                        "modified_at": modified_at,
                        "tags": list(tags),
                        "relevance_score": metadata.get("relevance_score", 0.0)
                    }
                })

            except Exception as e:
                logger.error(f"Error processing result: {e}")
                continue

        if not processed_results:
            return {
                "analysis": "No documents matched your filtering criteria.",
                "metadata": {
                    "total_documents": 0,
                    "date_range": f"{request.start_date} to {request.end_date}" if request.start_date and request.end_date else "all time",
                    "tags": request.tags if request.tags else "no tag filter",
                    "query": request.query,
                    "mode": request.mode
                }
            }
            
        # Generate analysis based on mode
        analysis = ""
        try:
            if request.mode == SearchMode.SUMMARY:
                # Sort by relevance score
                sorted_results = sorted(processed_results, 
                    key=lambda x: x["metadata"]["relevance_score"], 
                    reverse=True)
                
                analysis = "Summary of key documents:\n\n"
                for i, doc in enumerate(sorted_results[:5], 1):
                    content_preview = doc["content"][:200] + "..." if len(doc["content"]) > 200 else doc["content"]
                    analysis += f"{i}. {content_preview}\n"
                    if doc["metadata"].get("tags"):
                        analysis += f"   Tags: {', '.join(doc['metadata']['tags'])}\n"
                    analysis += "\n"
                    
            elif request.mode == SearchMode.TIMELINE:
                # Sort by date
                sorted_results = sorted(
                    [r for r in processed_results if r["metadata"].get("modified_at")],
                    key=lambda x: x["metadata"]["modified_at"]
                )
                
                analysis = "Document timeline:\n\n"
                for doc in sorted_results:
                    date = doc["metadata"]["modified_at"].split("T")[0]  # Just the date part
                    content_preview = doc["content"][:100] + "..." if len(doc["content"]) > 100 else doc["content"]
                    analysis += f"{date}: {content_preview}\n\n"
                    
            elif request.mode == SearchMode.TOPICS:
                # Group by tags
                topics = {}
                for doc in processed_results:
                    for tag in doc["metadata"].get("tags", []):
                        if tag not in topics:
                            topics[tag] = []
                        topics[tag].append(doc)
                
                analysis = "Topic analysis:\n\n"
                for tag, docs in sorted(topics.items()):
                    analysis += f"Topic: {tag}\n"
                    analysis += f"Documents: {len(docs)}\n"
                    # Show preview of most relevant document for each topic
                    if docs:
                        most_relevant = max(docs, key=lambda x: x["metadata"]["relevance_score"])
                        preview = most_relevant["content"][:100] + "..."
                        analysis += f"Sample: {preview}\n"
                    analysis += "\n"
                    
            elif request.mode == SearchMode.TRENDS:
                # Analyze document frequency over time
                time_bins = {}
                for doc in processed_results:
                    if doc["metadata"].get("modified_at"):
                        month = doc["metadata"].get("modified_at")[:7]  # YYYY-MM
                        time_bins[month] = time_bins.get(month, 0) + 1
                
                analysis = "Trend analysis:\n\n"
                for month in sorted(time_bins.keys()):
                    count = time_bins[month]
                    bar = "#" * min(count, 20)  # Visual bar capped at 20 chars
                    analysis += f"{month}: {bar} ({count} documents)\n"
                    
        except Exception as e:
            logger.error(f"Error generating analysis: {e}")
            analysis = f"Error generating {request.mode} analysis: {str(e)}"

        # Prepare final response
        response = {
            "analysis": analysis,
            "metadata": {
                "total_documents": len(processed_results),
                "date_range": f"{request.start_date} to {request.end_date}" if request.start_date and request.end_date else "all time",
                "tags": request.tags if request.tags else "no tag filter",
                "query": request.query,
                "mode": request.mode
            }
        }

        if request.include_raw:
            response["raw_results"] = processed_results  # Return all results
            
        return response

    except Exception as e:
        logger.exception("Deep search failed")
        return {
            "error": str(e),
            "metadata": {
                "query": request.query,
                "mode": request.mode,
                "error_details": str(e)
            }
        }

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
    "/cleanup-ignored",
    response_description='Remove documents from ignored directories'
)
async def cleanup_ignored():
    try:
        result = indexer.cleanup_ignored_files()
        logger.info(f"Cleanup result: {result}")
        return result
    except Exception as e:
        logger.error(f"Error in cleanup: {e}")
        return {"error": str(e)}

@router.post(
    "/cleanup-tags",
    response_description='Clean up and validate all tags in the index'
)
async def cleanup_tags():
    try:
        result = indexer.cleanup_tags()
        logger.info(f"Tag cleanup result: {result}")
        return result
    except Exception as e:
        logger.error(f"Error in tag cleanup: {e}")
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
