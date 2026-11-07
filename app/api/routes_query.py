from fastapi import APIRouter, HTTPException
from loguru import logger

from app.schemas.query import QueryRequest, QueryResponse
from app.services.rag_service import RAGService

router = APIRouter()

# Singleton service instance
_rag_service = None

def get_rag_service():
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service

@router.post("/query", response_model=QueryResponse)
async def query_fault_code(request: QueryRequest):
    """
    Endpoint for technicians to query fault codes with optional train class and subsystem filters.
    """
    try:
        service = get_rag_service()
        result = service.query(
            query_text=request.query,
            train_type=request.train_type,
            subsystem=request.subsystem,
            top_k=request.similarity_top_k or 5
        )
        return result
    except Exception as e:
        logger.error(f"Error querying fault code: {e}")
        raise HTTPException(status_code=500, detail=str(e))
