from pathlib import Path
from fastapi import APIRouter, HTTPException
from loguru import logger

from app.schemas.ingest import IngestRequest, IngestResponse
from app.services.ingestion import IngestionService
from app.api.routes_query import get_rag_service
from app.core.config import settings

router = APIRouter()
ingest_service = IngestionService()

@router.post("/ingest", response_model=IngestResponse)
async def ingest_manuals(request: IngestRequest):
    """
    Offline batch endpoint to parse, chunk, and index manuals into Qdrant.
    """
    try:
        rag = get_rag_service()
        target_path = Path(request.file_path) if request.file_path else settings.MANUALS_DIR
        
        if not target_path.is_absolute():
            target_path = settings.MANUALS_DIR / target_path

        if not target_path.exists():
            raise HTTPException(status_code=404, detail=f"Manual path does not exist: {target_path}")

        files_to_process = []
        if target_path.is_file():
            files_to_process.append(target_path)
        else:
            for ext in ("*.pdf", "*.md", "*.txt"):
                files_to_process.extend(target_path.glob(ext))

        if not files_to_process:
            return IngestResponse(
                status="warning",
                documents_processed=0,
                chunks_indexed=0,
                train_type=request.train_type,
                subsystem=request.subsystem,
                errors=["No compatible files found (.pdf, .md, .txt)"]
            )

        total_chunks = 0
        errors = []

        for f in files_to_process:
            try:
                manual_name = request.manual_name or f.stem
                docs = ingest_service.load_document(f)
                nodes = ingest_service.process_and_chunk(
                    docs=docs,
                    train_type=request.train_type or "General",
                    subsystem=request.subsystem or "General",
                    manual_name=manual_name,
                    document_category=request.document_category
                )
                upserted = rag.upsert_nodes(nodes)
                total_chunks += upserted
            except Exception as fe:
                msg = f"Failed processing file {f.name}: {fe}"
                logger.error(msg)
                errors.append(msg)

        return IngestResponse(
            status="completed" if not errors else "partial",
            documents_processed=len(files_to_process),
            chunks_indexed=total_chunks,
            train_type=request.train_type or "General",
            subsystem=request.subsystem or "General",
            document_category=request.document_category,
            errors=errors
        )
    except Exception as e:
        logger.error(f"Ingest failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
