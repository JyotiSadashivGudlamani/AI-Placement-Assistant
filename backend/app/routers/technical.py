"""
FastAPI router for Module 1: Technical Interview Preparation.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, status

from backend.app.schemas.technical import (
    TECHNICAL_TOPICS,
    DIFFICULTY_LEVELS,
    SaveQuestionRequest,
    SavedQuestionItem,
    SavedQuestionsListResponse,
    TechnicalQuestionRequest,
    TechnicalQuestionResponse,
)
from backend.app.services.technical_prep import TechnicalPrepService

router = APIRouter(prefix="/technical", tags=["Module 1: Technical Interview Preparation"])


@router.get("/topics", summary="List supported technical interview topics")
def get_topics():
    """Returns all 11 supported technical topics and difficulty levels."""
    return {
        "topics": TECHNICAL_TOPICS,
        "difficulties": DIFFICULTY_LEVELS,
    }


@router.post(
    "/generate",
    response_model=TechnicalQuestionResponse,
    summary="Generate a targeted technical interview question with explanation & code",
)
async def generate_technical_question(request: TechnicalQuestionRequest):
    """
    Generates a high-quality interview question for the selected topic and difficulty.
    Includes in-depth technical explanation, syntactically correct code sample,
    and follow-up interview questions.
    """
    service = TechnicalPrepService.get_instance()
    question_data = await service.generate_question(
        topic=request.topic,
        difficulty=request.difficulty,
        subtopic=request.subtopic,
        include_code=request.include_code,
    )
    return TechnicalQuestionResponse(**question_data)


@router.post(
    "/save",
    summary="Bookmark a technical interview question to MongoDB",
)
def save_technical_question(request: SaveQuestionRequest):
    """Saves a technical interview question for persistent student review."""
    service = TechnicalPrepService.get_instance()
    saved = service.save_question(request.model_dump())
    return {"message": "Question saved successfully.", "question": saved}


@router.get(
    "/saved",
    response_model=SavedQuestionsListResponse,
    summary="List saved technical interview questions",
)
def list_saved_questions(topic: Optional[str] = Query(default=None)):
    """Retrieves all bookmarked questions, optionally filtered by topic."""
    service = TechnicalPrepService.get_instance()
    questions = service.list_saved_questions(topic=topic)
    return SavedQuestionsListResponse(
        total=len(questions),
        questions=[SavedQuestionItem(**q) for q in questions],
    )


@router.delete(
    "/saved/{question_id}",
    summary="Delete a saved technical interview question",
)
def delete_saved_question(question_id: str):
    """Removes a bookmarked question from MongoDB."""
    service = TechnicalPrepService.get_instance()
    success = service.delete_saved_question(question_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Saved question '{question_id}' not found.",
        )
    return {"message": f"Question '{question_id}' deleted successfully."}
