import os
import logging
import asyncio
from indexer import Indexer
from pydantic import BaseModel
from async_queue import AsyncQueue
from fastapi import FastAPI, APIRouter
from contextlib import asynccontextmanager
from async_loop import index_loop, crawl_loop

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