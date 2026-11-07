# Thameslink Train Maintenance and Operations RAG Assistant

An on-premise, privacy-preserving Retrieval-Augmented Generation (RAG) assistant designed for railway technicians, maintenance engineers, and operations personnel. The system retrieves grounded technical procedures, fault code diagnoses, safety regulations, and general railway manual information with exact document and page citations.

The assistant runs locally on Apple Silicon (M1/M2/M3) using native Ollama with Metal GPU acceleration, Qdrant for hybrid dense and BM25 sparse retrieval, LlamaIndex for document chunking and vector storage, and n8n for chat orchestration and user interface.

---

## System Architecture

- User Interface and Orchestration: n8n Community Edition (running via Docker on port 5678)
- Backend Service: FastAPI (running on port 8000)
- RAG Framework: LlamaIndex (llama-index-core, llama-index-vector-stores-qdrant)
- Vector Database: Qdrant (port 6333, with hybrid dense vector plus BM25 keyword matching)
- PDF Extraction Engine: pypdfium2 (high-performance page-by-page extraction with accurate page boundaries)
- Local Models: Native macOS Ollama (qwen2.5:3b-instruct for generation and bge-m3 for embeddings)

---

## Prerequisites and Quickstart

### 1. Install and Start Ollama
Install Ollama for macOS to ensure Metal GPU hardware acceleration:
```bash
brew install --cask ollama
```

Pull the required generation and embedding models:
```bash
ollama pull qwen2.5:3b-instruct
ollama pull bge-m3
```

Make sure Ollama is running in the background.

### 2. Start Infrastructure Containers (Qdrant and n8n)
From the project root directory:
```bash
docker compose up -d
```
Verify services:
- Qdrant dashboard: http://localhost:6333/dashboard
- n8n interface: http://localhost:5678

### 3. Setup Python Virtual Environment
```bash
source .venv/bin/activate
pip install -r requirements.txt
```

### 4. Start the FastAPI RAG Backend
```bash
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## Document Ingestion Process

The ingestion pipeline parses documents (.pdf, .md, .txt), breaks them into structured semantic chunks, extracts verified page numbers, attaches file metadata, computes dense vectors in batches of 8, and upserts them into Qdrant.

### Automatic Deduplication and File Tagging
- Automatic File Name Tagging: You do not need to supply a manual name. Every chunk is automatically tagged with its physical source file name.
- True Page Numbering: Each chunk is mapped to its exact physical page number in the original PDF.
- Deduplication: Chunks already stored in Qdrant are detected automatically. Re-running ingestion skips existing documents and processes only newly added files.

### Option A: One-Command Batch Ingestion (Recommended)
Place all PDF, Markdown, or text manuals into the `data/manuals/` folder and run:
```bash
python scripts/ingest_all.py
```
The script will:
1. Scan `data/manuals/` for all supported files.
2. Check Qdrant and skip any manual already indexed.
3. Ingest, chunk, embed, and index all new files.
4. Report total chunks indexed across the entire library.

### Option B: Ingestion via API Endpoint
You can also trigger ingestion via HTTP POST request:

#### Ingest the entire manuals directory:
```bash
curl -X POST http://localhost:8000/api/v1/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "document_category": "general_reference"
  }'
```

#### Ingest a single specific document:
```bash
curl -X POST http://localhost:8000/api/v1/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "document_category": "general_reference",
    "file_path": "etcs_broschuere_ES64U2.pdf"
  }'
```

#### Ingest a fleet-specific maintenance manual:
```bash
curl -X POST http://localhost:8000/api/v1/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "train_type": "Class 700",
    "subsystem": "Traction",
    "document_category": "fleet_manual",
    "file_path": "class_700_traction_manual.pdf"
  }'
```

### Document Categories
- `general_reference`: For rulebooks, operating handbooks, standards, and technical specifications that apply across all fleets (e.g. ETCS documentation, GSM-R handbooks, Rule Book). Chunks marked with this category are always included in search results regardless of the fleet filter.
- `fleet_manual`: For maintenance manuals specific to a train class and subsystem.

---

## Inspecting and Managing Chunks

### Inspect Stored Chunks
To verify how pages and text were chunked and tagged:
```bash
# View the first 5 stored chunks
python scripts/inspect_chunks.py --limit 5

# Inspect chunks from a specific manual
python scripts/inspect_chunks.py --manual "ETCS" --limit 5

# Search for specific terms within the stored chunks
python scripts/inspect_chunks.py --search "ES64U2" --limit 3
```

You can also browse all stored chunks visually in the Qdrant Dashboard at http://localhost:6333/dashboard under the `train_manuals` collection.

### Reset the Vector Database
To wipe the collection and re-index clean:
```bash
python scripts/reset_collection.py
```

---

## Querying the Assistant

The assistant supports technical inquiries across maintenance, operations, and technical specifications. It enforces strict grounding: if the information is not present in the ingested manuals, it explicitly informs the user rather than hallucinating procedures.

### Types of Queries Supported

1. Fault Code Troubleshooting:
   - "How do I troubleshoot fault code FC 4103 on a Class 700?"
   - "What are the remedial steps for fault code FC 1205 door interlock loop open?"
   - The response provides fault diagnosis, safety precautions, numbered remedial steps, and circuit breaker or switch tags.

2. Technical Specifications and Equipment Descriptions:
   - "What is the ETCS equipment on the ES 64 U2 locomotive?"
   - "What are the electrical power supply ratings for the Class 700 traction inverter?"
   - "What are the main technical characteristics and weight of the ES64U2 with ETCS equipment?"

3. Operating Procedures and Handbooks:
   - "What are the driver registration procedures for GSM-R?"
   - "What are the rules for establishing an emergency call over GSM-R?"
   - "What is the procedure for resetting an emergency brake intervention?"

4. Regulatory and Safety Guidelines:
   - "What are the safety requirements before working on high voltage cubicles?"
   - "What are the trackside personal safety rules when working near conductor rails?"

### Querying via API
```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the ETCS equipment on the ES 64 U2?",
    "train_type": "General",
    "similarity_top_k": 5
  }'
```

### Querying via n8n Chat Interface
1. Open http://localhost:5678.
2. Open the imported workflow "Train Fault Code Troubleshooting Assistant".
3. Click on the Chat Trigger node and use the interactive chat window.
4. The assistant returns the direct technical answer followed by citation pills listing the manual name, section, and exact page number.
