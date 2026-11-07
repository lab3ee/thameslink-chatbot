import sys
from pathlib import Path

# Add project root to sys.path so 'app' can be imported from any working directory
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from qdrant_client import QdrantClient
from app.core.config import settings

def reset_collection():
    client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
    try:
        client.delete_collection(settings.QDRANT_COLLECTION)
        print(f"Collection '{settings.QDRANT_COLLECTION}' deleted successfully.")
    except Exception as e:
        print(f"Note: {e}")

if __name__ == "__main__":
    reset_collection()
