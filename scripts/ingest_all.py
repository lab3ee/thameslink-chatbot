import sys
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from app.core.config import settings
from app.services.ingestion import IngestionService
from app.services.rag_service import RAGService
from loguru import logger

def ingest_all():
    """
    Scans data/manuals/ and automatically ingests all .pdf, .md, and .txt files.
    Every chunk is tagged with its individual file name and exact page numbers.
    """
    manuals_dir = settings.MANUALS_DIR
    logger.info(f"Scanning directory for documents: {manuals_dir}")

    files_to_process = []
    for ext in ("*.pdf", "*.md", "*.txt"):
        files_to_process.extend(manuals_dir.glob(ext))

    if not files_to_process:
        logger.warning(f"No documents found in {manuals_dir}")
        return

    logger.info(f"Found {len(files_to_process)} document(s) to ingest: {[f.name for f in files_to_process]}")

    ingest_svc = IngestionService()
    rag_svc = RAGService()

    total_indexed = 0

    for f in sorted(files_to_process):
        # Check if this file has already been ingested in Qdrant
        if rag_svc.is_file_already_ingested(f.name):
            logger.info(f"Skipping already ingested file: {f.name}")
            continue

        logger.info(f"\n==================================================")
        logger.info(f"Processing new file: {f.name}")
        logger.info(f"==================================================")
        try:
            docs = ingest_svc.load_document(f)
            nodes = ingest_svc.process_and_chunk(
                docs=docs,
                train_type="General",
                subsystem="General",
                manual_name=f.name,
                document_category="general_reference",
                source_file_name=f.name
            )
            indexed_count = rag_svc.upsert_nodes(nodes)
            total_indexed += indexed_count
            logger.info(f"Finished {f.name}: {indexed_count} chunks indexed.")
        except Exception as e:
            logger.error(f"Failed processing {f.name}: {e}")

    logger.info(f"\nBatch ingestion finished! Total chunks indexed across all files: {total_indexed}\n")

if __name__ == "__main__":
    ingest_all()
