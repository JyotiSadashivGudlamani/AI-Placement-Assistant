"""
FastAPI router for Phase 6: LangGraph Agentic AI Assistant.
Routes student requests through the intelligent StateGraph orchestrator.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, status

from backend.app.agent.graph import run_placement_agent
from backend.app.db.mongo import MongoDBManager
from backend.app.schemas.agent import (
    AgentChatRequest,
    AgentChatResponse,
    AgentSessionDetail,
    AgentSessionListResponse,
    AgentSessionSummary,
    AgentTurnItem,
)

router = APIRouter(prefix="/agent", tags=["Phase 6: LangGraph Agentic AI Assistant"])


@router.post(
    "/chat",
    response_model=AgentChatResponse,
    summary="Chat with the LangGraph Placement Agent (Intelligent Request Routing)",
)
async def agent_chat(request: AgentChatRequest):
    """
    LangGraph Workflow:
    Student Request -> Request Classification -> Select Tool -> Execute Tool -> Synthesize -> Return Result.
    
    Automatically routes between:
    - Document RAG Question Answering
    - Resume Analysis & ATS Scanner
    - Job Description Matching & Gap Analysis
    - Technical Interview Question Generation
    - HR & Behavioral STAR Guidance
    - Aptitude Practice Testing
    - Mock Interview 5-Criteria Answer Evaluation
    - Fallback & Error Recovery
    """
    msg = request.message.strip()
    if not msg:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message cannot be empty.",
        )

    try:
        result = await run_placement_agent(
            user_request=msg,
            session_id=request.session_id,
            user_id=request.user_id,
            context=request.context,
        )
        return AgentChatResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent execution failed: {str(e)}",
        )


@router.get(
    "/sessions",
    response_model=AgentSessionListResponse,
    summary="List past LangGraph agent conversation sessions",
)
def list_agent_sessions(limit: int = Query(default=20, ge=1, le=50)):
    """Retrieves conversation thread summaries from MongoDB."""
    mongo = MongoDBManager.get_instance()
    if not mongo.is_connected:
        return AgentSessionListResponse(total=0, sessions=[])

    cursor = (
        mongo.db.agent_conversations.find({}, {"_id": 0})
        .sort("updated_at", -1)
        .limit(limit)
    )
    docs = list(cursor)
    items = [
        AgentSessionSummary(
            session_id=d["session_id"],
            created_at=d.get("created_at", ""),
            updated_at=d.get("updated_at", ""),
            last_request=d.get("last_request"),
            last_intent=d.get("last_intent"),
            turn_count=len(d.get("turns", [])),
        )
        for d in docs
    ]
    return AgentSessionListResponse(total=len(items), sessions=items)


@router.get(
    "/session/{session_id}",
    response_model=AgentSessionDetail,
    summary="Get full conversation turns and execution history for an agent session",
)
def get_agent_session_detail(session_id: str):
    """Retrieves full conversation turns and node execution paths for a thread."""
    mongo = MongoDBManager.get_instance()
    if not mongo.is_connected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MongoDB is not connected.",
        )

    doc = mongo.db.agent_conversations.find_one({"session_id": session_id}, {"_id": 0})
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent session '{session_id}' not found.",
        )

    turns = [
        AgentTurnItem(
            request=t.get("request", ""),
            intent=t.get("intent"),
            tool_name=t.get("tool_name"),
            response=t.get("response", ""),
            timestamp=t.get("timestamp", ""),
        )
        for t in doc.get("turns", [])
    ]

    return AgentSessionDetail(
        session_id=session_id,
        created_at=doc.get("created_at", ""),
        updated_at=doc.get("updated_at", ""),
        last_request=doc.get("last_request"),
        last_intent=doc.get("last_intent"),
        turns=turns,
    )


@router.get(
    "/workflow",
    summary="Get workflow architecture and graph specification",
)
def get_agent_workflow():
    """Returns the orchestrator graph topology and supported tools."""
    return {
        "graph_name": "PlacementPreparationStateGraph",
        "architecture": "Single Stateful Orchestrating Graph with Dynamic Conditional Routing",
        "state_model": "AgentState (TypedDict)",
        "memory_checkpointer": "MemorySaver (thread-scoped)",
        "persistence": "MongoDB (agent_conversations)",
        "nodes": [
            "classify",
            "rag_qa",
            "resume_analysis",
            "jd_analysis",
            "technical_prep",
            "hr_prep",
            "aptitude",
            "mock_interview_evaluation",
            "general_chat",
            "fallback",
            "synthesize",
        ],
        "tools": [
            "tool_rag_qa",
            "tool_resume_analysis",
            "tool_job_description_analysis",
            "tool_technical_prep",
            "tool_hr_prep",
            "tool_aptitude",
            "tool_mock_interview_evaluation",
        ],
        "diagram_mermaid": """
flowchart TD
    START([Student Request]) --> Classify[Node: Request Classification]
    Classify -->|rag_qa| ToolRAG[Tool: Document RAG Search]
    Classify -->|resume_analysis| ToolResume[Tool: Resume Analyser]
    Classify -->|jd_analysis| ToolJD[Tool: Job Description Matcher]
    Classify -->|technical_prep| ToolTech[Tool: Technical Question Generator]
    Classify -->|hr_prep| ToolHR[Tool: HR Behavioral Guidance]
    Classify -->|aptitude| ToolApt[Tool: Aptitude Practice Generator]
    Classify -->|mock_interview_evaluation| ToolMock[Tool: Interview Answer Evaluator]
    Classify -->|general_chat| ChatNode[Node: General Chat]
    Classify -->|invalid| FallbackNode[Node: Fallback & Instructions]

    ToolRAG --> Synthesize[Node: Response Synthesizer]
    ToolResume --> Synthesize
    ToolJD --> Synthesize
    ToolTech --> Synthesize
    ToolHR --> Synthesize
    ToolApt --> Synthesize
    ToolMock --> Synthesize

    Synthesize --> END([Return Result & Checkpoint State])
    ChatNode --> END
    FallbackNode --> END
"""
    }
