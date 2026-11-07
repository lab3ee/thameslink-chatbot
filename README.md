# Thameslink Train Technician Troubleshooting RAG Chatbot

An on-premise, privacy-preserving Retrieval-Augmented Generation (RAG) assistant designed to help railway maintenance technicians diagnose and troubleshoot train fault codes using official maintenance manuals.

Runs locally on Apple Silicon (M1/M2/M3, 8 GB RAM) using native Ollama with Metal GPU acceleration, Qdrant for hybrid search (dense + BM25 keyword matching), LlamaIndex for document chunking and retrieval, and n8n for workflow orchestration and chat UI.

---

## 🛠️ System Architecture

- **UI & Orchestration**: n8n Community Edition (`localhost:5678`)
- **Backend Service**: FastAPI (`localhost:8000`)
- **RAG Framework**: LlamaIndex (`llama-index-core`, `llama-index-vector-stores-qdrant`)
- **Vector Database**: Qdrant (`localhost:6333` with native sparse BM25 + dense hybrid search)
- **Local LLM & Embeddings**: Native Ollama (`qwen2.5:3b-instruct` + `bge-m3`)

---

## 🚀 Quickstart Guide

### 1. Install & Launch Native Ollama
```bash
brew install --cask ollama
# Pull required models
ollama pull qwen2.5:3b-instruct
ollama pull bge-m3
```

### 2. Start Supporting Services (Qdrant & n8n)
```bash
docker compose up -d
```
Verify Qdrant is accessible at `http://localhost:6333/dashboard` and n8n at `http://localhost:5678`.

### 3. Install Python Dependencies
```bash
source .venv/bin/activate
pip install -r requirements.txt
```

### 4. Start the RAG FastAPI Service
```bash
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 📚 Ingesting Maintenance Manuals

To ingest a manual or folder of manuals into Qdrant:
```bash
curl -X POST http://localhost:8000/api/v1/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "train_type": "Class 700",
    "subsystem": "Traction",
    "manual_name": "Class 700 Traction & Doors Troubleshooting",
    "file_path": "class_700_traction_and_doors_manual.md"
  }'
```

---

## 💬 Querying Fault Codes

Querying via API:
```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "FC 4103 inverter over-temperature",
    "train_type": "Class 700",
    "subsystem": "Traction"
  }'
```

---

## ⚙️ Importing into n8n
1. Open `http://localhost:5678`.
2. Go to **Workflows** > **Import from File**.
3. Select `n8n_workflows/train_troubleshooter_workflow.json`.
4. Test directly using the built-in n8n chat trigger test interface!
