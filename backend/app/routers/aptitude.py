"""
FastAPI router for Module 3: Aptitude Practice.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, status

from backend.app.schemas.aptitude import (
    APTITUDE_CATEGORIES,
    APTITUDE_CATEGORY_LABELS,
    AptitudeHistoryResponse,
    GenerateQuizRequest,
    GenerateQuizResponse,
    QuizResultResponse,
    SubmitQuizRequest,
)
from backend.app.services.aptitude_service import AptitudeService

router = APIRouter(prefix="/aptitude", tags=["Module 3: Aptitude Practice"])


@router.get("/categories", summary="List supported aptitude categories")
def get_categories():
    """Returns available aptitude categories and descriptions."""
    return {
        "categories": [
            {"id": cat_id, "label": APTITUDE_CATEGORY_LABELS.get(cat_id, cat_id)}
            for cat_id in APTITUDE_CATEGORIES
        ]
    }


@router.post(
    "/quiz/generate",
    response_model=GenerateQuizResponse,
    summary="Generate a practice aptitude quiz with randomized MCQs",
)
def generate_quiz(request: GenerateQuizRequest):
    """
    Generates an aptitude practice quiz with questions, options,
    and identifiers across Quantitative, Logical, or Verbal categories.
    """
    service = AptitudeService.get_instance()
    quiz = service.generate_quiz(
        category=request.category,
        difficulty=request.difficulty,
        count=request.count,
    )
    return GenerateQuizResponse(**quiz)


@router.post(
    "/quiz/submit",
    response_model=QuizResultResponse,
    summary="Submit quiz answers, get instant validation, scoring, and step-by-step explanations",
)
def submit_quiz(request: SubmitQuizRequest):
    """
    Validates submitted answers against ground truth, calculates score %,
    tracks time spent, provides step-by-step arithmetic/logical explanations,
    and logs the attempt to MongoDB.
    """
    service = AptitudeService.get_instance()
    answers_data = [a.model_dump() for a in request.answers]
    result = service.evaluate_quiz(
        category=request.category,
        answers=answers_data,
        time_taken_seconds=request.time_taken_seconds,
    )
    return result


@router.get(
    "/history",
    response_model=AptitudeHistoryResponse,
    summary="Get recent aptitude test history and score analytics",
)
def get_history(limit: int = Query(default=20, ge=1, le=50)):
    """Retrieves previous quiz scores, accuracy percentage, and time records from MongoDB."""
    service = AptitudeService.get_instance()
    history = service.get_history(limit=limit)
    return AptitudeHistoryResponse(total_attempts=len(history), history=history)
