"""
Chat router providing RAG question-answering with Ollama and ChromaDB retrieval.
"""

from uuid import uuid4
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status

from backend.app.core.config import settings
from backend.app.core.deps import get_optional_current_user
from backend.app.db.mongo import MongoDBManager
from backend.app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    Citation,
    MessageItem,
    SessionDetailResponse,
    SessionListResponse,
    SessionSummaryItem,
)
from backend.app.schemas.user import UserProfile
from backend.app.services.advanced_rag import AdvancedRAGService
from backend.app.services.llm import (
    LLMService,
    OllamaConnectionError,
    OllamaResponseError,
)
from backend.app.services.vector_store import VectorStoreService

router = APIRouter(tags=["Chat & Placement Q&A"])


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Ask an interview/placement preparation question grounded in indexed documents",
)
async def chat(
    request: ChatRequest,
    current_user: Optional[UserProfile] = Depends(get_optional_current_user),
):
    """
    RAG Pipeline:
    1. Embeds question or extracts keywords based on retrieval_mode.
    2. Retrieves top-K semantically relevant document chunks using Vector, BM25, Hybrid (RRF), or Cross-Encoder Reranking.
    3. Fetches prior conversation history for the session.
    4. Injects context and grounding instructions into Llama 3.2:3b.
    5. Returns grounded answer with exact source citations (filename, page number).
    6. Persists conversation turn in MongoDB.
    """
    question = request.question.strip()
    if not question:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question cannot be empty or pure whitespace.",
        )

    session_id = request.session_id or f"sess_{uuid4().hex[:12]}"
    rag_service = AdvancedRAGService.get_instance()
    llm = LLMService()
    mongo = MongoDBManager.get_instance()

    # 1. Build optional metadata filter for retrieval
    where_filter: Dict[str, Any] = {}
    if request.category:
        where_filter["category"] = request.category
    if request.document_id:
        where_filter["document_id"] = request.document_id

    # 2. Retrieve top-K chunks using selected mode (basic, vector, bm25, hybrid, hybrid_rerank)
    mode = request.retrieval_mode or "hybrid_rerank"
    retrieved_chunks = await rag_service.retrieve(
        query=question,
        mode=mode,
        top_k=request.top_k,
        where=where_filter if where_filter else None,
        use_multi_query=request.use_multi_query,
    )

    # 3. Check relevance
    has_context = len(retrieved_chunks) > 0

    # 4. Fetch prior conversation history if session exists
    history_messages: List[Dict[str, str]] = []
    if mongo.is_connected:
        session_data = mongo.get_conversation(session_id)
        if session_data:
            history_messages = [
                {"role": m.get("role", "user"), "content": m.get("content", "")}
                for m in session_data.get("messages", [])
            ]

    # 5. Generate answer using Ollama Llama 3.2:3b
    try:
        answer = await llm.generate_answer(
            question=question,
            context_chunks=retrieved_chunks,
            conversation_history=history_messages,
        )
    except OllamaConnectionError as err:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(err),
        )
    except OllamaResponseError as err:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(err),
        )

    # 6. Build verified citations (only from chunks actually retrieved)
    citations: List[Citation] = []
    seen_sources = set()

    # If the answer explicitly states information is not available, we don't present misleading citations
    negative_indicators = [
        "not contain sufficient information",
        "does not mention",
        "no information provided",
        "not available in the provided document",
    ]
    is_insufficient = any(phrase in answer.lower() for phrase in negative_indicators)

    if has_context and not is_insufficient:
        for chunk in retrieved_chunks:
            meta = chunk.get("metadata", {})
            filename = meta.get("filename", "unknown")
            page_number = int(meta.get("page_number", 1))
            similarity = float(chunk.get("similarity", 0.0))
            chunk_id = chunk.get("chunk_id", "")
            excerpt = chunk.get("text", "")[:180] + "..." if len(chunk.get("text", "")) > 180 else chunk.get("text", "")

            source_key = (filename, page_number)
            if source_key not in seen_sources:
                seen_sources.add(source_key)
                citations.append(
                    Citation(
                        filename=filename,
                        page_number=page_number,
                        chunk_id=chunk_id,
                        similarity=similarity,
                        excerpt=excerpt,
                    )
                )

    # 7. Persist turn in MongoDB with user ownership
    if mongo.is_connected:
        citation_dicts = [c.model_dump() for c in citations]
        owner_id = current_user.user_id if current_user else None
        mongo.save_chat_turn(
            session_id=session_id,
            question=question,
            answer=answer,
            citations=citation_dicts,
            user_id=owner_id,
        )

    return ChatResponse(
        session_id=session_id,
        question=question,
        answer=answer,
        citations=citations,
        retrieved_chunks_count=len(retrieved_chunks),
        has_document_context=has_context and not is_insufficient,
        retrieval_mode=mode,
    )


@router.get(
    "/chats",
    response_model=SessionListResponse,
    summary="List recent conversation sessions",
)
def list_chats(
    limit: int = 20,
    current_user: Optional[UserProfile] = Depends(get_optional_current_user),
):
    """Lists recent conversation sessions, scoped to authenticated user if logged in."""
    mongo = MongoDBManager.get_instance()
    if mongo.is_connected:
        user_id = current_user.user_id if current_user else None
        sessions = mongo.list_sessions(limit=limit, user_id=user_id)
        items = [
            SessionSummaryItem(
                session_id=s["session_id"],
                created_at=s.get("created_at", ""),
                updated_at=s.get("updated_at", ""),
                last_question=s.get("last_question"),
                message_count=s.get("message_count", 0),
            )
            for s in sessions
        ]
        return SessionListResponse(total=len(items), sessions=items)

    return SessionListResponse(total=0, sessions=[])


@router.get(
    "/chats/{session_id}",
    response_model=SessionDetailResponse,
    summary="Get full conversation history for a session",
)
def get_chat_session(
    session_id: str,
    current_user: Optional[UserProfile] = Depends(get_optional_current_user),
):
    """Retrieves message turn history, validating user ownership if session is owned."""
    mongo = MongoDBManager.get_instance()
    if not mongo.is_connected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MongoDB is not connected; session history is unavailable.",
        )

    session_data = mongo.get_conversation(session_id)
    if not session_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation session '{session_id}' not found.",
        )

    # Validate ownership if session is user-scoped
    sess_owner = session_data.get("user_id")
    if sess_owner and current_user and sess_owner != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. This conversation session belongs to another user.",
        )

    messages = [
        MessageItem(
            role=m.get("role", "user"),
            content=m.get("content", ""),
            timestamp=m.get("timestamp", ""),
            citations=[Citation(**c) for c in m.get("citations", [])] if m.get("citations") else None,
        )
        for m in session_data.get("messages", [])
    ]

    return SessionDetailResponse(
        session_id=session_id,
        created_at=session_data.get("created_at", ""),
        updated_at=session_data.get("updated_at", ""),
        last_question=session_data.get("last_question"),
        messages=messages,
    )


@router.delete(
    "/chats/{session_id}",
    summary="Delete a conversation session",
)
def delete_chat_session(
    session_id: str,
    current_user: Optional[UserProfile] = Depends(get_optional_current_user),
):
    """Clears history for a specific conversation session with permission check."""
    mongo = MongoDBManager.get_instance()
    if not mongo.is_connected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MongoDB is not connected.",
        )

    sess_data = mongo.get_conversation(session_id)
    if not sess_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found.",
        )

    sess_owner = sess_data.get("user_id")
    if sess_owner and current_user and sess_owner != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete this session.",
        )

    user_id = current_user.user_id if current_user else None
    success = mongo.delete_session(session_id, user_id=user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found.",
        )

    return {"message": f"Session '{session_id}' deleted successfully.", "session_id": session_id}
