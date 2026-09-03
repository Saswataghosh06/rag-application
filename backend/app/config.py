import os
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "RAG Application"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"
    
    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:3001",  "http://localhost:4040"]
    
    # LLM Configuration
    LLM_PROVIDER: str = "openai"  # openai | ollama
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3"
    
    # Embedding Configuration
    EMBEDDING_PROVIDER: str = "openai"  # openai | huggingface
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    HUGGINGFACE_EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    EMBEDDING_DIMENSIONS: int = 1536
    
    # Vector Database
    VECTOR_DB_PROVIDER: str = "qdrant"  # qdrant | chroma
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_COLLECTION: str = "documents"
    
    # Chunking
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    
    # Retrieval
    TOP_K: int = 5
    RERANK_ENABLED: bool = False
    RERANK_MODEL: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()