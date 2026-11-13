"""
Pydantic schemas for RAG chat, citations, and conversation sessions.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class Citation(BaseModel):
    filename: str
    page_number: int
    chunk_id: str
    similarity: float
    excerpt: Optional[str] = None


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, description="Student's interview/placement preparation question.")
    session_id: Optional[str] = Field(default=None, description="Conversation session ID for multi-turn history.")
    top_k: int = Field(default=4, ge=1, le=10, description="Configurable number of relevant chunks to retrieve.")
    category: Optional[str] = Field(default=None, description="Optional document category filter (e.g., 'placement', 'java').")
    document_id: Optional[str] = Field(default=None, description="Optional specific document ID filter.")
    retrieval_mode: Optional[str] = Field(
        default="hybrid_rerank",
        description="Retrieval engine: 'basic' (vector), 'bm25', 'hybrid', or 'hybrid_rerank'.",
    )
    use_multi_query: bool = Field(default=False, description="Enable multi-query generation and fusion.")


class ChatResponse(BaseModel):
    session_id: str
    question: str
    answer: str
    citations: List[Citation]
    retrieved_chunks_count: int
    has_document_context: bool
    retrieval_mode: str = "basic"


class MessageItem(BaseModel):
    role: str
    content: str
    timestamp: str
    citations: Optional[List[Citation]] = None


class SessionDetailResponse(BaseModel):
    session_id: str
    created_at: str
    updated_at: str
    last_question: Optional[str] = None
    messages: List[MessageItem]


class SessionSummaryItem(BaseModel):
    session_id: str
    created_at: str
    updated_at: str
    last_question: Optional[str] = None
    message_count: int


class SessionListResponse(BaseModel):
    total: int
    sessions: List[SessionSummaryItem]
