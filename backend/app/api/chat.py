from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import json
from typing import List, Dict

from app.models.schemas import ChatRequest, ChatResponse, SourceCitation
from app.services.rag_service import rag_service

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Non-streaming chat endpoint."""
    try:
        response, sources, conversation_id = await rag_service.query(
            query=request.query,
            top_k=request.top_k
        )
        
        return ChatResponse(
            message=response,
            sources=sources,
            conversation_id=conversation_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream")
async def chat_stream(request: ChatRequest):
    """Streaming chat endpoint using Server-Sent Events."""
    
    async def event_generator():
        try:
            async for event in rag_service.stream_query(
                query=request.query,
                top_k=request.top_k
            ):
                yield f"data: {json.dumps(event)}\n\n"
        except Exception as e:
            error_event = {"type": "error", "data": str(e)}
            yield f"data: {json.dumps(error_event)}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.post("/conversation")
async def chat_with_history(
    request: ChatRequest,
    history: List[Dict[str, str]]
):
    """Chat with conversation history for context."""
    try:
        response, sources, conversation_id = await rag_service.query(
            query=request.query,
            conversation_history=history,
            top_k=request.top_k
        )
        
        return ChatResponse(
            message=response,
            sources=sources,
            conversation_id=conversation_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))