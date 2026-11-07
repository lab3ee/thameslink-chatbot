import sys
import json
import argparse
from pathlib import Path

# Add project root to sys.path so 'app' can be imported reliably
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from qdrant_client import QdrantClient
from app.core.config import settings

def inspect_chunks(
    collection_name: str = settings.QDRANT_COLLECTION,
    manual_filter: str = None,
    limit: int = 10,
    search_keyword: str = None
):
    """
    Retrieves and displays stored chunks and metadata from Qdrant.
    """
    client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
    
    # Check collection existence
    try:
        info = client.get_collection(collection_name=collection_name)
        total_vectors = info.points_count or info.vectors_count or 0
        print(f"\n==================================================")
        print(f"Collection: '{collection_name}' | Total Stored Chunks: {total_vectors}")
        print(f"==================================================\n")
    except Exception as e:
        print(f"Error accessing collection '{collection_name}': {e}")
        return

    # Scroll points
    records, _ = client.scroll(
        collection_name=collection_name,
        limit=limit,
        with_payload=True,
        with_vectors=False
    )

    if not records:
        print("No chunks found in collection.")
        return

    count = 0
    for idx, record in enumerate(records, start=1):
        payload = record.payload or {}
        
        # In LlamaIndex, the payload text is usually in '_node_content' or directly in metadata
        content = ""
        metadata = {}
        
        if "_node_content" in payload:
            try:
                node_data = json.loads(payload["_node_content"])
                content = node_data.get("text", "")
                metadata = node_data.get("metadata", {})
            except Exception:
                content = str(payload.get("_node_content", ""))
        
        if not content and "text" in payload:
            content = payload["text"]
            metadata = {k: v for k, v in payload.items() if k != "text"}

        manual_name = metadata.get("manual_name", "N/A")
        page = metadata.get("page_number", "N/A")
        train_type = metadata.get("train_type", "N/A")
        subsystem = metadata.get("subsystem", "N/A")
        category = metadata.get("document_category", "N/A")

        # Apply filters if requested
        if manual_filter and manual_filter.lower() not in manual_name.lower():
            continue
        if search_keyword and search_keyword.lower() not in content.lower():
            continue

        count += 1
        print(f"--- [Chunk {count}] (ID: {record.id}) ---")
        print(f"Manual:   {manual_name}")
        print(f"Page:     {page} | Category: {category} | Train: {train_type} | Subsystem: {subsystem}")
        print(f"Preview:  {content[:300].strip()}...")
        print(f"{'-' * 50}\n")

    if count == 0:
        print("No chunks matched your filter criteria.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Inspect ingested document chunks in Qdrant.")
    parser.add_argument("--limit", type=int, default=5, help="Number of chunks to display (default: 5)")
    parser.add_argument("--manual", type=str, default=None, help="Filter chunks by manual name substring")
    parser.add_argument("--search", type=str, default=None, help="Search for specific keyword in chunk text")
    args = parser.parse_args()

    inspect_chunks(
        limit=args.limit,
        manual_filter=args.manual,
        search_keyword=args.search
    )
