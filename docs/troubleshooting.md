# Engineering Debugging & Environment Setup Log

> **The headline:** Setting up a full-stack Async Python + Next.js environment is rarely seamless. This document logs the actual engineering challenges encountered during the development of this platform and the exact solutions applied. Documenting these fixes proves the system was built and tested from the ground up.

## 1. Python Dependency Resolution Failure (`pandas`)

**The Error:**
`pip install -r requirements.txt` hung for 5+ minutes and crashed with:
`ERROR: Could not find a version that satisfies the requirement pandas==2.1.5`

**The Root Cause:**
Pandas version 2.1.5 does not exist. The library jumped from 2.1.4 to 2.2.0. Pip's dependency resolver was hanging while trying to find a non-existent version.

**The Fix:**
Updated `requirements.txt` to pin `pandas==2.1.4`. Also updated `pip` itself (`python -m pip install --upgrade pip`) to improve resolver speed.

---

## 2. Vector Database Client Incompatibility (`chromadb`)

**The Error:**
`AttributeError: module 'chromadb' has no attribute 'AsyncClient'` on application startup.

**The Root Cause:**
The original design attempted to use ChromaDB's async client, but the installed version of ChromaDB (0.4.22) does not support `AsyncClient()` natively in the way it was being called.

**The Fix:**
Instead of downgrading or patching the ChromaDB API, the vector service was refactored to use **Qdrant's local embedded mode**. 
* Changed `AsyncQdrantClient(url=...)` to `AsyncQdrantClient(path="qdrant_data")`.
* This allowed the app to run without Docker (saving the vector store to a local folder) while remaining fully asynchronous.

---

## 3. FastAPI Async File Upload TypeError

**The Error:**
`TypeError: 'async for' requires an object with __aiter__ method, got SpooledTemporaryFile` when uploading a document.

**The Root Cause:**
The file upload handler was using `async for chunk in file.file:`. In FastAPI, `file.file` is a standard synchronous `SpooledTemporaryFile`. Using `async for` on a synchronous object crashes Python.

**The Fix:**
Replaced the async iteration with FastAPI's native async read method:
```python
# Before
async for chunk in file.file: ...

# After
content = await file.read()
file_size = len(content)
```

---

## 4. Windows Port Exclusion (`EACCES`)

**The Error:**
Next.js failed to start with `Error: listen EACCES: permission denied 0.0.0.0:3000` (and also failed on port 3001).

**The Root Cause:**
Windows Hyper-V and WSL (Windows Subsystem for Linux) reserve massive, dynamic ranges of TCP ports for their own internal use. Ports 3000 and 3001 were caught in these reserved exclusion ranges.

**The Fix:**
1. Verified the excluded port ranges using: `netsh interface ipv4 show excludedportrange protocol=tcp`.
2. Started the Next.js development server on an unreserved, higher port: `npm run dev -- -p 4040`.
3. Updated the FastAPI `CORS_ORIGINS` in `config.py` to explicitly allow `http://localhost:4040`.

---

## 5. OpenAI API Rate Limiting (429 Too Many Requests)

**The Error:**
Document ingestion failed with `Client error '429 Too Many Requests' for url 'https://api.openai.com/v1/embeddings'`.

**The Root Cause:**
OpenAI was rejecting the embedding API requests due to hitting a rate limit or exhausted free trial credits on the test account.

**The Fix:**
To ensure the application is 100% free to run and test, the system was pivoted to local, open-source models:
* `EMBEDDING_PROVIDER` changed to `huggingface` (`all-MiniLM-L-6-v2`).
* `LLM_PROVIDER` changed to `ollama` (`llama3`).
* Cleared the old Qdrant database (`rm -r -force qdrant_data`) because the vector dimensions changed from 1536 (OpenAI) to 384 (HuggingFace), which would have caused Qdrant to crash on dimension mismatch.
```