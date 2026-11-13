"""
FastAPI router for Module 6: Mock Interview.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, status

from backend.app.schemas.mock_interview import (
    MockInterviewHistoryItem,
    MockInterviewHistoryResponse,
    MockInterviewSessionDetail,
    StartInterviewRequest,
    StartInterviewResponse,
    SubmitAnswerRequest,
    SubmitAnswerResponse,
)
from backend.app.services.mock_interview_service import MockInterviewService

router = APIRouter(prefix="/mock-interview", tags=["Module 6: Mock Interview"])


@router.post(
    "/start",
    response_model=StartInterviewResponse,
    summary="Start a new interactive mock interview session",
)
async def start_mock_interview(request: StartInterviewRequest):
    """
    Initializes a new mock interview session (Technical or HR),
    sets difficulty level and question budget, and returns Question 1.
    """
    service = MockInterviewService.get_instance()
    session = await service.start_session(
        interview_type=request.interview_type,
        topic=request.topic,
        difficulty=request.difficulty,
        total_questions=request.total_questions,
    )
    return StartInterviewResponse(**session)


@router.post(
    "/{session_id}/answer",
    response_model=SubmitAnswerResponse,
    summary="Submit student answer, receive 5-criteria evaluation, and get next question",
)
async def submit_interview_answer(session_id: str, request: SubmitAnswerRequest):
    """
    Evaluates the student's answer across:
    1. Correctness (1-10)
    2. Relevance (1-10)
    3. Completeness (1-10)
    4. Clarity (1-10)
    5. Communication (1-10)
    Provides actionable critique, improved model answer, and generates next question or final summary.
    """
    service = MockInterviewService.get_instance()
    try:
        result = await service.submit_answer(
            session_id=session_id,
            student_answer=request.student_answer,
        )
        return SubmitAnswerResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Interview evaluation error: {str(e)}",
        )


@router.get(
    "/{session_id}",
    response_model=MockInterviewSessionDetail,
    summary="Get full mock interview transcript and score card",
)
def get_mock_interview_session(session_id: str):
    """Retrieves full conversation turns, scores, and summary report for a session."""
    service = MockInterviewService.get_instance()
    session = service.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mock interview session '{session_id}' not found.",
        )
    return MockInterviewSessionDetail(**session)


@router.get(
    "s/history",
    response_model=MockInterviewHistoryResponse,
    summary="List past mock interview sessions and performance records",
)
def list_mock_interview_history(limit: int = Query(default=20, ge=1, le=50)):
    """Lists past interview sessions with completion status and overall average scores."""
    service = MockInterviewService.get_instance()
    sessions = service.list_sessions(limit=limit)
    items = [
        MockInterviewHistoryItem(
            session_id=s["session_id"],
            interview_type=s.get("interview_type", "technical"),
            topic=s.get("topic", "General"),
            difficulty=s.get("difficulty", "medium"),
            status=s.get("status", "in_progress"),
            total_questions=s.get("total_questions", 3),
            completed_questions=s.get("completed_questions", 0),
            average_score=s.get("average_score"),
            created_at=s.get("created_at", ""),
        )
        for s in sessions
    ]
    return MockInterviewHistoryResponse(total=len(items), sessions=items)
