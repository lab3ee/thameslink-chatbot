from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.core.config import settings
from app.api.routes_query import router as query_router
from app.api.routes_ingest import router as ingest_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="On-prem RAG API for railway technicians troubleshooting fault codes from technical manuals.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(query_router, prefix=settings.API_V1_STR, tags=["Query"])
app.include_router(ingest_router, prefix=settings.API_V1_STR, tags=["Ingestion"])

@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "ollama_endpoint": settings.OLLAMA_BASE_URL,
        "qdrant_endpoint": f"{settings.QDRANT_HOST}:{settings.QDRANT_PORT}"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
