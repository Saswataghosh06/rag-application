from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import get_settings
from app.api import chat, documents
from app.services.rag_service import rag_service

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize RAG service
    await rag_service.initialize()
    print("RAG service initialized successfully")
    yield
    # Shutdown: Cleanup if needed
    print("Shutting down...")


app = FastAPI(
    title=settings.APP_NAME,
    description="Full-Stack RAG Application API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat.router, prefix=settings.API_V1_PREFIX)
app.include_router(documents.router, prefix=settings.API_V1_PREFIX)


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "llm_provider": settings.LLM_PROVIDER,
        "vector_db": settings.VECTOR_DB_PROVIDER,
        "embedding_provider": settings.EMBEDDING_PROVIDER
    }


@app.get("/")
async def root():
    return {
        "message": "RAG Application API",
        "docs": "/docs",
        "health": "/health"
    }