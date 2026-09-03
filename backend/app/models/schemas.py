from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class MessageType(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class DocumentUploadResponse(BaseModel):
    id: str
    filename: str
    chunks_created: int
    status: str
    message: str


class DocumentInfo(BaseModel):
    id: str
    filename: str
    upload_date: datetime
    chunk_count: int
    file_size: int


class SourceCitation(BaseModel):
    chunk_id: str
    document_id: str
    document_name: str
    content: str
    page_number: Optional[int] = None
    score: float


class ChatMessage(BaseModel):
    role: MessageType
    content: str
    sources: Optional[list[SourceCitation]] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    conversation_id: Optional[str] = None
    top_k: Optional[int] = None


class ChatResponse(BaseModel):
    message: str
    sources: list[SourceCitation]
    conversation_id: str
    tokens_used: Optional[dict] = None


class ConversationHistory(BaseModel):
    conversation_id: str
    messages: list[ChatMessage]
    created_at: datetime
    updated_at: datetime