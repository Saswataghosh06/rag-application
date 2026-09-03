from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from typing import List
import os
import tempfile
from pathlib import Path

from app.models.schemas import DocumentUploadResponse, DocumentInfo
from app.services.rag_service import rag_service

router = APIRouter(prefix="/documents", tags=["documents"])


async def process_document(file_path: str, filename: str, file_size: int):
    """Background task to process uploaded document."""
    try:
        # Extract text based on file type
        text = await extract_text(file_path, filename)
        
        if not text or len(text.strip()) < 10:
            print(f"Document {filename} has insufficient text content")
            return
        
        # Ingest into RAG
        doc_id, chunks = await rag_service.ingest_document(
            text=text,
            filename=filename,
            file_size=file_size
        )
        print(f"Successfully ingested {filename}: {chunks} chunks created")
        
    except Exception as e:
        print(f"Error processing {filename}: {str(e)}")
    finally:
        # Cleanup temp file
        if os.path.exists(file_path):
            os.remove(file_path)


async def extract_text(file_path: str, filename: str) -> str:
    """Extract text from various file formats."""
    suffix = Path(filename).suffix.lower()
    
    if suffix == ".txt" or suffix == ".md":
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    
    elif suffix == ".pdf":
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(file_path)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            return text
        except ImportError:
            raise HTTPException(
                status_code=500,
                detail="PDF support requires PyMuPDF. Install with: pip install PyMuPDF"
            )
    
    elif suffix == ".docx":
        try:
            from docx import Document
            doc = Document(file_path)
            return "\n".join([para.text for para in doc.paragraphs])
        except ImportError:
            raise HTTPException(
                status_code=500,
                detail="DOCX support requires python-docx. Install with: pip install python-docx"
            )
    
    elif suffix in [".csv"]:
        import pandas as pd
        df = pd.read_csv(file_path)
        return df.to_string()
    
    elif suffix in [".json"]:
        import json
        with open(file_path, "r") as f:
            data = json.load(f)
        return json.dumps(data, indent=2)
    
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format: {suffix}. Supported: .txt, .md, .pdf, .docx, .csv, .json"
        )


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """Upload and process a document for RAG."""
    # Validate file type
    allowed_extensions = {".txt", ".md", ".pdf", ".docx", ".csv", ".json"}
    file_ext = Path(file.filename).suffix.lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file_ext}. Allowed: {', '.join(allowed_extensions)}"
        )
    
    # Validate file size (50MB limit)
    max_size = 50 * 1024 * 1024
    content = await file.read()
    file_size = len(content)
    
    if file_size > max_size:
        raise HTTPException(status_code=400, detail="File too large. Max 50MB.")
    
    # Save to temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp:
        tmp.write(content)
        tmp_path = tmp.name
    
    # Generate a preliminary ID (actual ID created during processing)
    import uuid
    doc_id = str(uuid.uuid4())
    
    # Process in background
    background_tasks.add_task(
        process_document,
        tmp_path,
        file.filename,
        file_size
    )
    
    return DocumentUploadResponse(
        id=doc_id,
        filename=file.filename,
        chunks_created=0,  # Will be updated after processing
        status="processing",
        message=f"Document '{file.filename}' uploaded and is being processed"
    )


@router.get("/", response_model=List[DocumentInfo])
async def list_documents():
    """List all uploaded documents."""
    docs = await rag_service.list_documents()
    return [
        DocumentInfo(
            id=doc["id"],
            filename=doc["filename"],
            upload_date=doc.get("upload_date", ""),
            chunk_count=doc["chunk_count"],
            file_size=doc.get("file_size", 0)
        )
        for doc in docs
    ]


@router.delete("/{document_id}")
async def delete_document(document_id: str):
    """Delete a document and all its chunks."""
    success = await rag_service.delete_document(document_id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"message": f"Document {document_id} deleted successfully"}