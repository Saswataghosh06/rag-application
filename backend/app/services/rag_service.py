from typing import List, Dict, Any, AsyncGenerator, Optional, Tuple
from uuid import uuid4
from datetime import datetime
import asyncio

from app.config import get_settings
from app.utils.chunking import DocumentChunker, Chunk
from app.services.embedding_service import get_embedding_provider, EmbeddingProvider
from app.services.vector_service import VectorService, SearchResult
from app.services.llm_service import get_llm_provider, LLMProvider
from app.models.schemas import SourceCitation


# System prompt for RAG
RAG_SYSTEM_PROMPT = """You are a helpful AI assistant that answers questions based on the provided context documents.

## Instructions:
1. Answer the user's question using ONLY the information from the provided context.
2. If the context doesn't contain enough information to answer the question, say so clearly.
3. Cite your sources by referencing the document name and section when possible.
4. Be concise but thorough in your answers.
5. If you're unsure about something, acknowledge the uncertainty.
6. Format your response in a clear, readable way using markdown when appropriate.

## Context Documents:
{context}

## Important:
- Never make up information not present in the context.
- Always indicate when you're citing a specific source.
"""


class RAGService:
    """Core RAG orchestration service."""
    
    def __init__(self):
        self.settings = get_settings()
        self.chunker = DocumentChunker(
            chunk_size=self.settings.CHUNK_SIZE,
            chunk_overlap=self.settings.CHUNK_OVERLAP,
            strategy="recursive"
        )
        self.embedding_provider: Optional[EmbeddingProvider] = None
        self.vector_service: Optional[VectorService] = None
        self.llm_provider: Optional[LLMProvider] = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize all services."""
        if self._initialized:
            return
        
        self.embedding_provider = get_embedding_provider()
        self.vector_service = VectorService()
        await self.vector_service.initialize()
        self.llm_provider = get_llm_provider()
        self._initialized = True
    
    async def ingest_document(
        self,
        text: str,
        filename: str,
        file_size: int,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, int]:
        """
        Ingest a document into the RAG system.
        Returns: (document_id, chunks_created)
        """
        await self.initialize()
        
        document_id = str(uuid4())
        base_metadata = {
            "filename": filename,
            "file_size": file_size,
            "upload_date": datetime.now().isoformat(),
            "document_id": document_id,
        }
        if metadata:
            base_metadata.update(metadata)
        
        # Step 1: Chunk the document
        chunks = self.chunker.chunk_document(text, base_metadata)
        
        # Step 2: Generate embeddings (batch for efficiency)
        chunk_texts = [chunk.content for chunk in chunks]
        embeddings = await self.embedding_provider.embed_batch(chunk_texts)
        
        # Step 3: Store in vector database
        chunks_created = await self.vector_service.add_documents(
            chunks=chunks,
            embeddings=embeddings,
            document_id=document_id
        )
        
        return document_id, chunks_created
    
    async def query(
        self,
        query: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        top_k: Optional[int] = None,
        document_ids: Optional[List[str]] = None
    ) -> Tuple[str, List[SourceCitation], str]:
        """
        Query the RAG system.
        Returns: (response, sources, conversation_id)
        """
        await self.initialize()
        
        conversation_id = str(uuid4())
        top_k = top_k or self.settings.TOP_K
        
        # Step 1: Generate query embedding
        query_embedding = await self.embedding_provider.embed_text(query)
        
        # Step 2: Retrieve relevant chunks
        search_results = await self.vector_service.search(
            query_embedding=query_embedding,
            top_k=top_k,
            document_ids=document_ids,
            score_threshold=0.3
        )
        
        # Step 3: Build context from retrieved chunks
        context_parts = []
        sources = []
        
        for i, result in enumerate(search_results):
            doc_name = result.metadata.get("filename", "Unknown Document")
            page = result.metadata.get("page_number")
            location = f" (Page {page})" if page else ""
            
            context_parts.append(
                f"[Document {i+1}: {doc_name}{location}]\n{result.content}"
            )
            
            sources.append(SourceCitation(
                chunk_id=result.id,
                document_id=result.metadata.get("document_id", ""),
                document_name=doc_name,
                content=result.content[:500] + "..." if len(result.content) > 500 else result.content,
                page_number=page,
                score=result.score
            ))
        
        context = "\n\n---\n\n".join(context_parts)
        
        # Step 4: Build messages for LLM
        messages = [
            {
                "role": "system",
                "content": RAG_SYSTEM_PROMPT.format(context=context)
            }
        ]
        
        # Add conversation history if provided
        if conversation_history:
            messages.extend(conversation_history[-6:])  # Keep last 6 messages for context
        
        messages.append({"role": "user", "content": query})
        
        # Step 5: Generate response
        response = await self.llm_provider.generate(messages, temperature=0.3)
        
        return response, sources, conversation_id
    
    async def stream_query(
        self,
        query: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        top_k: Optional[int] = None,
        document_ids: Optional[List[str]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Streaming query - yields chunks as they're generated.
        Yields: {"type": "token"|"sources"|"done", "data": ...}
        """
        await self.initialize()
        
        conversation_id = str(uuid4())
        top_k = top_k or self.settings.TOP_K
        
        # Step 1 & 2: Embed and retrieve
        query_embedding = await self.embedding_provider.embed_text(query)
        search_results = await self.vector_service.search(
            query_embedding=query_embedding,
            top_k=top_k,
            document_ids=document_ids,
            score_threshold=0.3
        )
        
        # Step 3: Build context
        context_parts = []
        sources = []
        
        for i, result in enumerate(search_results):
            doc_name = result.metadata.get("filename", "Unknown Document")
            page = result.metadata.get("page_number")
            location = f" (Page {page})" if page else ""
            
            context_parts.append(
                f"[Document {i+1}: {doc_name}{location}]\n{result.content}"
            )
            
            sources.append(SourceCitation(
                chunk_id=result.id,
                document_id=result.metadata.get("document_id", ""),
                document_name=doc_name,
                content=result.content[:500] + "..." if len(result.content) > 500 else result.content,
                page_number=page,
                score=result.score
            ))
        
        context = "\n\n---\n\n".join(context_parts)
        
        # Send sources first
        yield {
            "type": "sources",
            "data": [s.model_dump() for s in sources],
            "conversation_id": conversation_id
        }
        
        # Step 4 & 5: Build messages and stream response
        messages = [
            {
                "role": "system",
                "content": RAG_SYSTEM_PROMPT.format(context=context)
            }
        ]
        
        if conversation_history:
            messages.extend(conversation_history[-6:])
        
        messages.append({"role": "user", "content": query})
        
        async for token in self.llm_provider.stream_generate(messages, temperature=0.3):
            yield {
                "type": "token",
                "data": token
            }
        
        yield {"type": "done", "data": None}
    
    async def delete_document(self, document_id: str) -> bool:
        """Delete a document from the RAG system."""
        await self.initialize()
        await self.vector_service.delete_document(document_id)
        return True
    
    async def list_documents(self) -> List[Dict[str, Any]]:
        """List all documents in the RAG system."""
        await self.initialize()
        return await self.vector_service.list_documents()


# Singleton instance
rag_service = RAGService()