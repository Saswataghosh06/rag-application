# System Architecture & Engineering Design

> **The headline:** The architecture is built on a strict separation of concerns. The frontend handles UI state and stream consumption, while the backend abstracts LLM, Embedding, and Vector providers behind interfaces, allowing the system to pivot between cloud (OpenAI) and local (Ollama/HuggingFace) deployments via a single `.env` variable.

## 1. Architectural Philosophy

Building a RAG application is relatively easy; building one that is scalable, maintainable, and vendor-agnostic is difficult. The architecture of this platform is modeled after enterprise Dependency Injection patterns. 

The core philosophy is: **The business logic (RAG orchestration) should never know which LLM or Vector Database it is talking to.** 

By abstracting these behind base classes, the application avoids vendor lock-in. An enterprise can switch from OpenAI to a local, air-gapped Llama-3 deployment simply by changing a single environment variable, without rewriting a single line of pipeline logic.

---

## 2. High-Level Data Flow Architecture

The system is divided into two primary asynchronous flows: **Document Ingestion** (the write path) and **Query & Generation** (the read path). Both paths are designed to be non-blocking.

### 2.1 Document Ingestion Sequence (Write Path)
```text
[Next.js Client] 
      │
      │ 1. POST /api/v1/documents/upload (multipart/form-data)
      ▼
[FastAPI Router] 
      │
      │ 2. Validate file type & size
      │ 3. Write to SpooledTemporaryFile
      │ 4. Return 200 OK ("Processing started")  ────────► [Next.js Client] (UI unblocked)
      │
      ▼
[BackgroundTask: process_document]
      │
      ├─► 5. Extract Text (PyMuPDF / python-docx)
      │
      ├─► 6. Recursive Character Chunking (1000 chars, 200 overlap)
      │
      ├─► 7. Embedding Provider (OpenAI / HuggingFace)
      │      (Generates 1536d or 384d vectors)
      │
      └─► 8. Qdrant Vector DB (Upsert vectors + metadata payloads)
```

**Why Asynchronous Background Tasks?**
PDF extraction and batch embedding are CPU and I/O intensive. If FastAPI handled this synchronously, the HTTP connection would time out, and the Next.js UI would freeze. By offloading to `BackgroundTasks`, the API remains responsive for other users while the heavy lifting happens in the background.

### 2.2 Query & Generation Sequence (Read Path via SSE)
```text
[Next.js Client]
      │
      │ 1. POST /api/v1/chat/stream (Query: "What is the Q3 revenue?")
      ▼
[FastAPI Router]
      │
      ├─► 2. Embedding Provider (Embeds user query into vector space)
      │
      ├─► 3. Qdrant Vector DB (Cosine Similarity Search, Top-K=5, Threshold=0.3)
      │      (Returns relevant text chunks + metadata)
      │
      ├─► 4. Prompt Constructor (Injects chunks into strict System Prompt)
      │
      └─► 5. LLM Provider (OpenAI / Ollama)
             │
             │ 6. AsyncGenerator: Yields tokens one-by-one
             ▼
[FastAPI StreamingResponse]
      │
      │ 7. Formats tokens as Server-Sent Events (SSE): "data: {token}\n\n"
      ▼
[Next.js Client]
      (ReadableStream reads SSE and updates React state in real-time)
```

---

## 3. Backend Design: The Provider Pattern

To ensure the system is modular, the backend uses Abstract Base Classes (ABCs) for its core AI components. This is the same pattern used in enterprise cloud SDKs (like AWS Boto3 or LangChain).

### 3.1 LLM Provider Abstraction
The `LLMProvider` base class defines standard methods for generation. Any new LLM (e.g., Anthropic Claude, Google Gemini) can be added by simply creating a new class that inherits from this base.

```python
class LLMProvider(ABC):
    @abstractmethod
    async def generate(self, messages: List[Dict[str, str]], temperature: float) -> str: pass
    
    @abstractmethod
    async def stream_generate(self, messages: List[Dict[str, str]], temperature: float) -> AsyncGenerator[str, None]: pass
```

**Implemented Providers:**
* **OpenAIProvider:** Uses `httpx.AsyncClient` to stream tokens from the OpenAI Chat Completions API. It handles JSON parsing of the `data: [DONE]` SSE format.
* **OllamaProvider:** Uses `httpx.AsyncClient` to stream from the local Ollama REST API (`/api/chat`). This allows 100% private, offline RAG.

### 3.2 Runtime Dependency Injection
At runtime, the `get_llm_provider()` factory function reads the `.env` file and instantiates the correct class. The RAG orchestrator (`rag_service.py`) calls this factory, meaning it is completely agnostic to the underlying LLM.

```python
def get_llm_provider() -> LLMProvider:
    settings = get_settings()
    if settings.LLM_PROVIDER == "openai":
        return OpenAIProvider()
    elif settings.LLM_PROVIDER == "ollama":
        return OllamaProvider()
    else:
        raise ValueError(f"Unknown LLM provider")
```

---

## 4. Vector Storage: Qdrant Local Embedded Mode

Instead of forcing the user to install Docker and spin up a separate database server just to test the application, the architecture utilizes Qdrant's **Local Embedded Mode**.

```python
self._client = AsyncQdrantClient(path="qdrant_data")
```
This allows the high-performance Rust-based Qdrant engine to run directly inside the Python process, saving the vectors to a local directory (`qdrant_data/`). 

### 4.1 Vector Schema & Metadata Payload
When vectors are inserted into Qdrant, they are accompanied by a rich JSON payload. This metadata is what powers the "Source Citations" in the UI.

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "vector": [0.012, -0.045, 0.887, ... 1536 dimensions],
  "payload": {
    "content": "The total revenue for Q3 was $15.8M...",
    "document_id": "doc-uuid-1234",
    "filename": "Q3_Financial_Report.pdf",
    "page_number": 4,
    "chunk_index": 12,
    "upload_date": "2024-05-20T14:30:00Z"
  }
}
```

### 4.2 Production Architecture Trade-off
| Mode | Configuration | Use Case |
|---|---|---|
| **Local Embedded** | `AsyncQdrantClient(path="qdrant_data")` | Portfolio development, single-node testing, zero-Docker setup. |
| **Distributed** | `AsyncQdrantClient(url="http://qdrant:6333")` | Production, multi-user concurrency, horizontal scaling. |

Because the client is abstracted behind `VectorService`, moving from local development to a distributed Docker production environment requires changing **one line of code**.

---

## 5. Frontend Design: Native SSE Consumption

Many Next.js applications use heavy client-side libraries (like `socket.io` or `EventSource`) for real-time chat. This architecture uses the native Fetch API's `ReadableStream` to consume the FastAPI Server-Sent Events stream. This reduces bundle size and gives finer control over the stream.

```typescript
const reader = response.body?.getReader();
const decoder = new TextDecoder();
let buffer = '';

while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  
  buffer += decoder.decode(value, { stream: true });
  const lines = buffer.split('\n');
  buffer = lines.pop() || '';

  for (const line of lines) {
    if (line.startsWith('data: ')) {
      const event: StreamEvent = JSON.parse(line.slice(6));
      // Update React state with new token
    }
  }
}
```

### Why SSE over WebSockets?
LLM token generation is strictly unidirectional (Server → Client). WebSockets add unnecessary overhead for bi-directional communication. SSE is lighter, handles auto-reconnection natively, and integrates perfectly with FastAPI's `StreamingResponse`.

---

## 6. Tech Stack Mapping

| Layer | Technology | Architectural Role |
|---|---|---|
| **Frontend** | Next.js 14, Tailwind | UI rendering, drag-and-drop file handling, native SSE stream consumption. |
| **API Gateway** | FastAPI, Uvicorn | Async request handling, Pydantic data validation, background task offloading. |
| **Service Layer** | Python Abstract Classes | Decouples core logic from AI/Vector vendors (Provider Pattern). |
| **Vector DB** | Qdrant (Local) | High-performance cosine similarity search with metadata filtering. |
| **LLM / Embeddings** | OpenAI / Ollama / HF | Pluggable AI models for generation and vectorization. |
```
