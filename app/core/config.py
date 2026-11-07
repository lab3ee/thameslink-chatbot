from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    PROJECT_NAME: str = "Thameslink Train Fault Code Troubleshooting RAG"
    API_V1_STR: str = "/api/v1"
    
    # Ollama settings (native macOS)
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    LLM_MODEL: str = "qwen2.5:3b-instruct"
    EMBED_MODEL: str = "bge-m3"
    LLM_TEMPERATURE: float = 0.1
    LLM_REQUEST_TIMEOUT: float = 120.0
    
    # Qdrant settings
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_COLLECTION: str = "train_manuals"
    
    # Ingestion settings
    CHUNK_SIZE: int = 600
    CHUNK_OVERLAP: int = 80
    MANUALS_DIR: Path = Path(__file__).resolve().parent.parent.parent / "data" / "manuals"
    
    # Retrieval settings
    SIMILARITY_TOP_K: int = 5
    SPARSE_TOP_K: int = 5
    HYBRID_ALPHA: float = 0.5  # 0.0 = BM25 sparse only, 1.0 = dense vector only

    # Grounding: minimum retrieval score to consider a chunk relevant enough to send to the LLM.
    # Chunks below this threshold are discarded before generation.
    # Range is typically 0.0–1.0; raise if hallucinations persist, lower if too many "not found" on valid queries.
    MIN_RELEVANCE_SCORE: float = 0.30

    # Embedding batch size for ingestion.
    # Larger batches are faster but use more RAM. On 8 GB M1, 8–16 is a safe range.
    # Reduce to 4 if you see memory pressure warnings during ingestion of large documents.
    EMBED_BATCH_SIZE: int = 8

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
