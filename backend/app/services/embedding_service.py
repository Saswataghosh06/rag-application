from typing import List
from abc import ABC, abstractmethod
import httpx
from app.config import get_settings


class EmbeddingProvider(ABC):
    @abstractmethod
    async def embed_text(self, text: str) -> List[float]:
        pass
    
    @abstractmethod
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        pass


class OpenAIEmbeddingProvider(EmbeddingProvider):
    def __init__(self):
        self.settings = get_settings()
        self.api_key = self.settings.OPENAI_API_KEY
        self.model = self.settings.OPENAI_EMBEDDING_MODEL
        self.base_url = "https://api.openai.com/v1"
    
    async def embed_text(self, text: str) -> List[float]:
        results = await self.embed_batch([text])
        return results[0]
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/embeddings",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "input": texts
                }
            )
            response.raise_for_status()
            data = response.json()
            return [item["embedding"] for item in sorted(data["data"], key=lambda x: x["index"])]


class HuggingFaceEmbeddingProvider(EmbeddingProvider):
    def __init__(self):
        from sentence_transformers import SentenceTransformer
        self.settings = get_settings()
        self.model = SentenceTransformer(self.settings.HUGGINGFACE_EMBEDDING_MODEL)
    
    async def embed_text(self, text: str) -> List[float]:
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        embeddings = self.model.encode(texts, convert_to_numpy=True, batch_size=32)
        return embeddings.tolist()


def get_embedding_provider() -> EmbeddingProvider:
    settings = get_settings()
    if settings.EMBEDDING_PROVIDER == "openai":
        return OpenAIEmbeddingProvider()
    elif settings.EMBEDDING_PROVIDER == "huggingface":
        return HuggingFaceEmbeddingProvider()
    else:
        raise ValueError(f"Unknown embedding provider: {settings.EMBEDDING_PROVIDER}")