"""
Pydantic schemas for Phase 6 LangGraph Agentic AI Assistant.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AgentChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="Student's prompt or request to the agent.")
    session_id: Optional[str] = Field(default=None, description="Thread/session ID for conversation memory.")
    user_id: Optional[str] = Field(default=None, description="User ID for privacy-scoped data access.")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Optional extra context parameters.")


class AgentChatResponse(BaseModel):
    session_id: str
    user_request: str
    intent: str
    intent_confidence: float
    tool_used: Optional[str] = None
    response: str
    citations: Optional[List[Dict[str, Any]]] = None
    suggested_actions: Optional[List[str]] = None
    execution_path: List[str] = []


class AgentTurnItem(BaseModel):
    request: str
    intent: Optional[str] = None
    tool_name: Optional[str] = None
    response: str
    timestamp: str


class AgentSessionDetail(BaseModel):
    session_id: str
    created_at: str
    updated_at: str
    last_request: Optional[str] = None
    last_intent: Optional[str] = None
    turns: List[AgentTurnItem] = []


class AgentSessionSummary(BaseModel):
    session_id: str
    created_at: str
    updated_at: str
    last_request: Optional[str] = None
    last_intent: Optional[str] = None
    turn_count: int


class AgentSessionListResponse(BaseModel):
    total: int
    sessions: List[AgentSessionSummary]
