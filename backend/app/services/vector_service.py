from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from uuid import uuid4
from app.config import get_settings
from app.utils.chunking import Chunk


@dataclass
class SearchResult:
    id: str
    content: str
    metadata: Dict[str, Any]
    score: float


class VectorService:
    """Abstraction over vector database operations."""
    
    def __init__(self):
        self.settings = get_settings()
        self._client = None
        self._collection = None
    
    async def initialize(self):
        """Initialize connection and ensure collection exists."""
        if self.settings.VECTOR_DB_PROVIDER == "qdrant":
            await self._init_qdrant()
        elif self.settings.VECTOR_DB_PROVIDER == "chroma":
            await self._init_chroma()
    
    async def _init_qdrant(self):
        from qdrant_client import AsyncQdrantClient
        from qdrant_client.models import Distance, VectorParams
        
        self._client = AsyncQdrantClient(path="qdrant_data")
        
        # Check if collection exists, create if not
        collections = await self._client.get_collections()
        collection_names = [c.name for c in collections.collections]
        
        if self.settings.QDRANT_COLLECTION not in collection_names:
            await self._client.create_collection(
                collection_name=self.settings.QDRANT_COLLECTION,
                vectors_config=VectorParams(
                    size=self.settings.EMBEDDING_DIMENSIONS,
                    distance=Distance.COSINE
                )
            )
        
        self._collection = self.settings.QDRANT_COLLECTION
    
    async def _init_chroma(self):
        import chromadb
        self._client = chromadb.AsyncClient()
        self._collection = await self._client.get_or_create_collection(
            name=self.settings.QDRANT_COLLECTION,
            metadata={"hnsw:space": "cosine"}
        )
    
    async def add_documents(
        self,
        chunks: List[Chunk],
        embeddings: List[List[float]],
        document_id: str
    ) -> int:
        """Add chunked documents with embeddings to the vector store."""
        if self.settings.VECTOR_DB_PROVIDER == "qdrant":
            return await self._add_qdrant(chunks, embeddings, document_id)
        elif self.settings.VECTOR_DB_PROVIDER == "chroma":
            return await self._add_chroma(chunks, embeddings, document_id)
    
    async def _add_qdrant(
        self,
        chunks: List[Chunk],
        embeddings: List[List[float]],
        document_id: str
    ) -> int:
        from qdrant_client.models import PointStruct
        
        points = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            point_id = str(uuid4())
            chunk.metadata["document_id"] = document_id
            chunk.metadata["point_id"] = point_id
            
            points.append(PointStruct(
                id=point_id,
                vector=embedding,
                payload={
                    "content": chunk.content,
                    **chunk.metadata
                }
            ))
        
        # Batch upload
        await self._client.upsert(
            collection_name=self._collection,
            points=points
        )
        
        return len(points)
    
    async def _add_chroma(
        self,
        chunks: List[Chunk],
        embeddings: List[List[float]],
        document_id: str
    ) -> int:
        ids = []
        documents = []
        metadatas = []
        
        for i, chunk in enumerate(chunks):
            chunk_id = str(uuid4())
            chunk.metadata["document_id"] = document_id
            
            ids.append(chunk_id)
            documents.append(chunk.content)
            metadatas.append(chunk.metadata)
        
        await self._collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )
        
        return len(ids)
    
    async def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        document_ids: Optional[List[str]] = None,
        score_threshold: float = 0.0
    ) -> List[SearchResult]:
        """Search for similar documents."""
        if self.settings.VECTOR_DB_PROVIDER == "qdrant":
            return await self._search_qdrant(query_embedding, top_k, document_ids, score_threshold)
        elif self.settings.VECTOR_DB_PROVIDER == "chroma":
            return await self._search_chroma(query_embedding, top_k, document_ids, score_threshold)
    
    async def _search_qdrant(
        self,
        query_embedding: List[float],
        top_k: int,
        document_ids: Optional[List[str]],
        score_threshold: float
    ) -> List[SearchResult]:
        from qdrant_client.models import Filter, FieldCondition, MatchAny
        
        query_filter = None
        if document_ids:
            query_filter = Filter(
                must=[
                    FieldCondition(
                        key="document_id",
                        match=MatchAny(any=document_ids)
                    )
                ]
            )
        
        results = await self._client.query_points(
            collection_name=self._collection,
            query=query_embedding,
            limit=top_k,
            query_filter=query_filter,
            with_payload=True
        )
        
        search_results = []
        for point in results.points:
            if point.score >= score_threshold:
                search_results.append(SearchResult(
                    id=str(point.id),
                    content=point.payload["content"],
                    metadata=point.payload,
                    score=point.score
                ))
        
        return search_results
    
    async def _search_chroma(
        self,
        query_embedding: List[float],
        top_k: int,
        document_ids: Optional[List[str]],
        score_threshold: float
    ) -> List[SearchResult]:
        where_filter = None
        if document_ids:
            where_filter = {"document_id": {"$in": document_ids}}
        
        results = await self._collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_filter,
            include=["documents", "metadatas", "distances"]
        )
        
        search_results = []
        if results["ids"] and results["ids"][0]:
            for i, (doc_id, doc, metadata, distance) in enumerate(zip(
                results["ids"][0],
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0]
            )):
                score = 1 - distance  # Convert distance to similarity
                if score >= score_threshold:
                    search_results.append(SearchResult(
                        id=doc_id,
                        content=doc,
                        metadata=metadata,
                        score=score
                    ))
        
        return search_results
    
    async def delete_document(self, document_id: str) -> int:
        """Delete all chunks for a document."""
        if self.settings.VECTOR_DB_PROVIDER == "qdrant":
            from qdrant_client.models import Filter, FieldCondition, MatchValue
            
            await self._client.delete(
                collection_name=self._collection,
                points_selector=Filter(
                    must=[
                        FieldCondition(
                            key="document_id",
                            match=MatchValue(value=document_id)
                        )
                    ]
                )
            )
            return 1
        elif self.settings.VECTOR_DB_PROVIDER == "chroma":
            await self._collection.delete(
                where={"document_id": document_id}
            )
            return 1
    
    async def list_documents(self) -> List[Dict[str, Any]]:
        """List all unique documents in the store."""
        # This is a simplified implementation
        if self.settings.VECTOR_DB_PROVIDER == "qdrant":
            # Scroll through all points and extract unique document_ids
            all_docs = {}
            offset = None
            while True:
                results, offset = await self._client.scroll(
                    collection_name=self._collection,
                    limit=100,
                    offset=offset,
                    with_payload=True,
                    with_vectors=False
                )
                
                for point in results:
                    doc_id = point.payload.get("document_id")
                    if doc_id and doc_id not in all_docs:
                        all_docs[doc_id] = {
                            "id": doc_id,
                            "filename": point.payload.get("filename", "unknown"),
                            "chunk_count": 0
                        }
                    if doc_id:
                        all_docs[doc_id]["chunk_count"] += 1
                
                if offset is None:
                    break
            
            return list(all_docs.values())
        
        return []