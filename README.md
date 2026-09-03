<div align="center">
 <img width="1584" height="396" alt="Image" src="https://github.com/user-attachments/assets/70569313-7e4e-4950-a0b4-2e2681336c9f" />
</div>

<h1 align="center">Enterprise RAG Intelligence Platform</h1>
<h3 align="center">Technical Case Study — Building a Production-Grade Retrieval-Augmented Generation System</h3>

<p align="center">
  <img alt="status" src="https://img.shields.io/badge/status-portfolio_case_study-1E56C7">
  <img alt="stack" src="https://img.shields.io/badge/stack-Next.js_%7C_FastAPI_%7C_Qdrant_%7C_Ollama-1E56C7">
  <img alt="ai" src="https://img.shields.io/badge/LLM-Llama3_%7C_GPT--4o-12A879">
  <img alt="retrieval" src="https://img.shields.io/badge/retrieval-SSE_Streaming_%7C_Semantic_Chunking-8B98AE">
</p>

<p align="center"><b>Saswata Ghosh</b><br>
<a href="https://github.com/Saswataghosh06/rag-application">GitHub Repo</a> · <a href="https://www.linkedin.com/in/saswata-ghosh06/">LinkedIn</a> · <a href="mailto:saswataghosh2022@gmail.com">Email</a></p>

---

> **The headline:** Large Language Models hallucinate because they lack enterprise context. This full-stack RAG platform solves that by ingesting unstructured documents (PDF, DOCX, CSV), chunking them semantically, embedding them into a Qdrant vector database, and streaming cited, grounded responses to a Next.js frontend with sub-second latency.

---

### Quick Navigation

**Strategy & Impact:** [Executive Summary](#1-executive-summary) → [The Enterprise Search Problem](#2-the-enterprise-search-problem) → [Product Overview](#3-product-overview)

**Architecture & Engineering:** [System Architecture](#4-system-architecture) → [The RAG Pipeline Deep Dive](#5-the-rag-pipeline-deep-dive) → [Tech Stack](#6-tech-stack)

**Trade-offs & Code:** [Technical Decisions](#7-technical-decisions--trade-offs) → [UI Showcase](#8-ui-showcase) → [Future Roadmap](#9-production-readiness--future-roadmap)

---

## 1. Executive Summary

Enterprise knowledge is trapped in silos—dense PDFs, technical manuals, and internal wikis. Standard keyword search fails to understand semantic intent, and handing proprietary data to public LLMs raises severe security and hallucination concerns. 

This project is a full-stack **Retrieval-Augmented Generation (RAG)** application designed to act as a secure, internal AI assistant. It allows users to upload documents and ask complex questions, receiving token-by-token streaming responses complete with **exact source citations** (document name, page number, and relevance score).

| Metric / Feature | Implementation |
|---|---:|
| **Frontend Stack** | Next.js 14 (App Router), Tailwind CSS, SSE Streaming |
| **Backend Stack** | FastAPI (Python 3.11), Async Endpoints, Pydantic Validation |
| **Vector Database** | Qdrant (Local Embedded Mode for zero-Docker dev) |
| **LLM Provider (Cloud)** | OpenAI `gpt-4o` via Async HTTPX |
| **LLM Provider (Local)** | Ollama `llama3` (100% private, offline inference) |
| **Embedding Strategy** | OpenAI `text-embedding-3-small` (1536d) / HuggingFace `all-MiniLM-L-6-v2` (384d) |
| **Chunking Strategy** | Recursive Character (1000 tokens, 200 overlap) |
| **Retrieval Mechanism** | Cosine Similarity, Top-K = 5, Score Thresholding |
| **Document Support** | PDF (PyMuPDF), DOCX (python-docx), CSV, TXT, MD, JSON |

---

## 2. The Enterprise Search Problem

In a typical enterprise, finding a specific answer requires opening dozens of documents and using `Ctrl+F`. Standard LLMs cannot solve this because:
1. **Hallucination:** They generate plausible but factually incorrect answers.
2. **Context Limits:** You cannot paste a 500-page PDF into a standard prompt window.
3. **Data Privacy:** Sending proprietary company data to public APIs is often a compliance violation.

### The Objective
Build a production-grade architecture that connects an LLM to a private set of documents. The system must guarantee that **100% of AI responses are grounded in retrieved context**, complete with document citations, while providing a ChatGPT-like user experience via real-time token streaming.

---

## 3. Product Overview

The application is split into a highly responsive Next.js frontend and a robust FastAPI backend.

* **Document Ingestion:** Users can drag & drop files. The backend instantly returns a `200 OK` while extracting text and generating embeddings in a background task, ensuring the UI never freezes.
* **Semantic Chat:** Users ask questions in natural language. The app streams the AI's response token-by-token.
* **Transparent Citations:** Every AI response includes an expandable "Sources" panel. Users can click to see the exact chunk of text, the document name, the page number, and the cosine similarity score the AI used to formulate its answer.

---

## 4. System Architecture

<div align="center">
<img width="100%" alt="Architecture Diagram" src="YOUR_ARCHITECTURE_DIAGRAM_URL" />
<br><sub>Next.js Client → FastAPI (Async) → Embedding Model → Qdrant Vector DB → LLM → SSE Stream</sub>
</div>

The architecture follows a strict separation of concerns:
1. **Client Layer (Next.js):** Handles UI state, file uploads, and consumes the Server-Sent Events (SSE) stream using native `fetch` and `ReadableStream` APIs.
2. **API Gateway (FastAPI):** Handles routing, CORS, file validation (50MB limit), and delegates heavy processing to background tasks.
3. **Service Layer (Python):** Abstracted providers for LLMs, Embeddings, and Vector Stores. This allows swapping between OpenAI and Ollama without rewriting core logic.
4. **Persistence Layer (Qdrant):** Stores high-dimensional vectors and JSON payloads (metadata) for fast cosine similarity lookups.

---

## 5. The RAG Pipeline Deep Dive

### 5.1 Document Ingestion & Pre-processing
When a file is uploaded, `BackgroundTasks` in FastAPI trigger the `process_document` pipeline.
* **PDF Extraction:** Uses `PyMuPDF` to extract text while preserving page numbers for citations.
* **DOCX Extraction:** Uses `python-docx` to pull text paragraph by paragraph.

### 5.2 Advanced Recursive Chunking Strategy
Naive chunking (splitting by fixed character count) breaks sentences and loses semantic meaning. This platform uses a custom **Recursive Character Text Splitter**.
It attempts to split by paragraphs (`\n\n`), then sentences (`. `), then words (` `). 
* **Chunk Size:** 1000 tokens
* **Overlap:** 200 tokens (ensures context bleeds over into the next chunk, preventing critical information from being split in half).

### 5.3 Vectorization & Storage
Chunks are converted to vectors using HuggingFace's `all-MiniLM-L-6-v2` (running locally for zero-cost) or OpenAI's API. They are stored in Qdrant with rich metadata payloads: `{filename, page_number, chunk_id, upload_date}`.

### 5.4 Retrieval & Grounded Generation
1. The user's query is embedded.
2. Qdrant performs a cosine similarity search, retrieving the `Top 5` most relevant chunks (score > 0.3).
3. A strict system prompt is injected:
   > *"You are a helpful AI assistant. Answer the user's question using ONLY the information from the provided context documents. If the context doesn't contain enough information, say so clearly. Never make up information."*

### 5.5 Server-Sent Events (SSE) Streaming
To eliminate the "loading..." delay, the FastAPI backend uses `StreamingResponse`. As the LLM generates tokens, they are yielded back to the Next.js client instantly, creating a ChatGPT-like typing effect. 

---

## 6. Tech Stack

| Layer | Technology | Why it was chosen |
|---|---|---|
| **Frontend** | Next.js 14, Tailwind | App Router, server components, and seamless SSE consumption via React hooks. |
| **Backend** | FastAPI, Python 3.11 | Native async support for concurrent API calls and high-performance HTTP handling. |
| **Vector DB** | Qdrant | High-performance cosine similarity search with robust metadata filtering. |
| **LLM (Cloud)** | OpenAI `gpt-4o` | High reasoning capability for complex document synthesis. |
| **LLM (Local)** | Ollama `llama3` | 100% private, offline-capable RAG for sensitive enterprise documents. |
| **Embeddings** | Sentence-Transformers / OpenAI | Flexibility to switch between local (free) and cloud (fast) embedding generation. |

---

## 7. Technical Decisions & Trade-offs

| Decision | Alternative Considered | Why This Choice |
|---|---|---|
| **FastAPI + SSE** | WebSockets | SSE is simpler for unidirectional streaming (server → client) which is perfect for LLM token generation. WebSockets add unnecessary complexity for bi-directional chat. |
| **Qdrant (Local Path)** | ChromaDB / Pinecone | Qdrant's local mode allows the entire app to run without Docker for development, while offering a clear path to production via Docker compose. |
| **Custom Recursive Chunker** | LangChain Chunkers | Building a custom chunker reduces dependency bloat and gives exact control over overlap logic, keeping the backend lightweight. |
| **Async Document Upload** | Synchronous processing | PDF extraction and embedding generation are CPU/IO heavy. Background tasks prevent blocking the FastAPI event loop, returning a `200 OK` instantly. |
| **Provider Abstraction** | Hardcoded LLM calls | Abstracting LLM and Embedding providers behind base classes means the system can switch from OpenAI to local Ollama by changing a single `.env` variable. |

---

## 8. UI Showcase

<div align="center">
<<img width="1366" height="768" alt="Image" src="https://github.com/user-attachments/assets/d4655d1a-d3ca-4e90-948f-042dc56f76aa" />
<br><sub>Streaming AI responses with transparent, expandable source citations.</sub>
</div>

<br>
<div align="center">
<img width="1366" height="768" alt="Image" src="https://github.com/user-attachments/assets/c07b74b6-4238-45cc-86f8-7a1a46a93c18" />
<br><sub>Drag-and-drop ingestion with background processing.</sub>
</div>

---

## 9. Production Readiness & Future Roadmap

While this acts as a portfolio case study, it is built to production standards. Future enhancements to reach full enterprise deployment include:

| Priority | Enhancement | Why it matters |
|---|---|---|
| **Do First** | Cross-Encoder Reranking | Retrieve Top 20 chunks, rerank with `ms-marco-MiniLM`, pass Top 5 to LLM. Drastically reduces hallucination. |
| **Do First** | Redis Conversation History | Currently stateless. Adding Redis will allow multi-turn conversations with context. |
| **Next** | RAGAS Evaluation Pipeline | Implement metrics for Faithfulness, Answer Relevancy, and Context Precision. |
| **Next** | NextAuth.js + JWT | Add role-based access control (RBAC) so users only query documents they have permissions for. |
| **Next** | Docker Compose Orchestration | Fully containerize Qdrant, Backend, and Frontend for 1-click deployment. |

---

## 10. How to Run Locally

```bash
# 1. Clone the repository
git clone https://github.com/Saswataghosh06/rag-application.git
cd rag-application

# 2. Backend Setup
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt

# Setup environment variables
cp .env.example .env
# Edit .env with your OpenAI API key OR Ollama URL

# Run the backend
uvicorn app.main:app --reload --port 8000

# 3. Frontend Setup (in a new terminal)
cd frontend
npm install

# Setup frontend environment
echo "NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1" > .env.local

# Run the frontend
npm run dev
```
Visit `http://localhost:3000` (or the port specified in your terminal) to access the application.

---

## Deep Dive Documentation

To keep this executive summary concise, the in-depth technical specifications and engineering logs have been modularized into the `docs/` directory.

| Document | What's in it |
|---|---|
| [`docs/architecture.md`](./docs/architecture.md) | Deep dive into the Backend/Frontend async architecture, sequence diagrams, and the Provider Pattern. |
| [`docs/rag_pipeline.md`](./docs/rag_pipeline.md) | The math and logic behind recursive chunking, vectorization, cosine similarity, and prompt engineering. |
| [`docs/troubleshooting.md`](./docs/troubleshooting.md) | Real engineering debugging logs (Fixing 429 Rate Limits, Windows Port EACCES, Async File Uploads). |

---

<p align="center"><sub>Questions about the architecture, the chunking strategy, or the SSE implementation? Happy to walk through the code.</sub></p>
