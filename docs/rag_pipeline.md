# The RAG Pipeline: Chunking, Retrieval, & Generation

> **The headline:** A naive RAG implementation will split documents randomly, retrieve the top results, and trust the LLM to figure it out. This platform uses a custom recursive chunking algorithm, metadata-rich vector payloads, cosine similarity score thresholding, and strict prompt engineering to minimize hallucinations and maximize citation accuracy.

## 1. Document Ingestion & Text Extraction

The pipeline begins with raw file ingestion. To support enterprise use cases (e.g., legal contracts, technical manuals), the backend extracts text asynchronously without blocking the API thread.

### 1.1 Extraction Logic
The system uses Python's premier libraries to parse unstructured data:
* **PDF (`PyMuPDF / fitz`):** Extracts text while preserving page numbers. This is critical for downstream citations.
* **DOCX (`python-docx`):** Extracts text paragraph by paragraph.
* **CSV (`pandas`):** Flattens tabular data into a string representation.

```python
# documents.py - PDF Extraction preserving page numbers
import fitz  # PyMuPDF

async def extract_text(file_path: str, filename: str) -> str:
    if filename.endswith('.pdf'):
        doc = fitz.open(file_path)
        text = ""
        for page_num, page in enumerate(doc):
            # Extract text and append page number metadata
            text += f"\n[Page {page_num + 1}]\n"
            text += page.get_text()
        doc.close()
        return text
```

---

## 2. Recursive Character Chunking (Deep Dive)

If you split a document every 1000 characters (naive chunking), you will frequently cut sentences in half. This destroys semantic meaning and confuses the LLM during retrieval. 

### 2.1 The Algorithm
This platform uses a custom **Recursive Character Text Splitter**. It attempts to split text using a priority list of separators, keeping semantically related text together:

```python
# chunking.py
separators = ["\n\n", "\n", ". ", " ", ""]
```

1. First, it tries to split by paragraph (`\n\n`).
2. If the resulting chunks are still larger than `chunk_size`, it splits those chunks by new lines (`\n`).
3. Then by sentence ends (`. `), then by words (` `).
4. As a last resort, it hard-splits by character.

### 2.2 The Overlap Strategy
**Configuration:**
* `chunk_size`: 1000 characters
* `chunk_overlap`: 200 characters

The 200-character overlap ensures that if a critical piece of information sits right on the boundary of a split, it will be included in *both* the current chunk and the next chunk. 

### 2.3 Metadata Enrichment
As chunks are created, the chunker attaches vital metadata to each one, tracking its exact position in the original document:

```python
# chunking.py
chunk_metadata = {
    **metadata,
    "chunk_index": i,
    "chunk_length": len(chunk_text),
    "start_char": start_pos,
    "end_char": end_pos,
}
```

---

## 3. Vectorization & Embeddings

Text chunks are converted to numerical vectors (arrays of floats). The system supports two modes via the Provider Pattern:

### 3.1 Provider Comparison

| Provider | Model | Dimensions | Speed | Privacy | Cost |
|---|---|---|---|---|---|
| **OpenAI** | `text-embedding-3-small` | 1536 | Fast | Cloud (External) | $0.02 / 1M tokens |
| **HuggingFace** | `all-MiniLM-L-6-v2` | 384 | Medium (CPU) | 100% Local | Free |

### 3.2 Vector Schema & Metadata Payload
When vectors are inserted into Qdrant, they are accompanied by a rich JSON payload. This metadata is what powers the "Source Citations" in the UI.

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "vector": [0.012, -0.045, 0.887, ... 1536 or 384 dimensions],
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

---

## 4. Semantic Retrieval

When a user asks a question, the query is embedded into the same vector space. Qdrant then performs a **Cosine Similarity Search**.

### 4.1 Why Cosine Similarity?
Cosine similarity measures the angle between two vectors, rather than their magnitude. 

Formula: $Cosine(A, B) = \frac{A \cdot B}{||A|| \times ||B||}$

This means a short user query ("What was Q3 revenue?") can successfully match a longer, detailed chunk in the document ("The total revenue for the third quarter was $15.8M, driven mostly by...") because their semantic *direction* is identical, even though their lengths (magnitudes) are vastly different.

### 4.2 Score Thresholding (Anti-Hallucination)
The system is configured to retrieve the Top 5 (`TOP_K=5`) chunks, but it filters out low-quality matches using a `score_threshold = 0.3`. 

```python
# vector_service.py
results = await self._client.query_points(
    collection_name=self._collection,
    query=query_embedding,
    limit=top_k,
    query_filter=query_filter,
    with_payload=True
)

search_results = []
for point in results.points:
    if point.score >= score_threshold:  # 0.3 filter
        search_results.append(SearchResult(...))
```

**Why 0.3?** If the highest matching chunk has a score of 0.25, the system will tell the user "I don't know" rather than passing irrelevant context to the LLM. This is a critical, engineered defense against hallucinations.

---

## 5. Prompt Engineering & Grounded Generation

The retrieved chunks are injected into a strict System Prompt. This is the final layer of defense against hallucinations.

### 5.1 The RAG System Prompt
```text
You are a helpful AI assistant that answers questions based on the provided context documents.

## Instructions:
1. Answer the user's question using ONLY the information from the provided context.
2. If the context doesn't contain enough information to answer the question, say so clearly.
3. Cite your sources by referencing the document name and section when possible.
4. Be concise but thorough in your answers.
5. If you're unsure about something, acknowledge the uncertainty.
6. Format your response in a clear, readable way using markdown when appropriate.

## Important:
- Never make up information not present in the context.
- Always indicate when you're citing a specific source.
```

### 5.2 Context Formatting
The retrieved chunks are formatted with their document names and page numbers before being injected into the prompt:

```text
[Document 1: Q3_Financial_Report.pdf (Page 4)]
The total revenue for Q3 was $15.8M, driven mostly by...

[Document 2: Q3_Financial_Report.pdf (Page 12)]
Operating expenses decreased by 4% year-over-year...
```

This strict instruction, combined with the formatted context chunks, grounds the LLM. The LLM is no longer guessing based on its pre-training data; it is acting purely as a reasoning and summarization engine over the provided text.
```
