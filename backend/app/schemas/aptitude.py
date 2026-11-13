"""
Pydantic schemas for Module 3: Aptitude Practice.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


APTITUDE_CATEGORIES = ["quantitative", "logical", "verbal", "all"]

APTITUDE_CATEGORY_LABELS = {
    "quantitative": "Quantitative Aptitude",
    "logical": "Logical Reasoning",
    "verbal": "Verbal Ability",
    "all": "Comprehensive Mix (Quant + Logical + Verbal)",
}


class MCQOption(BaseModel):
    key: str = Field(..., description="Option label: A, B, C, or D")
    text: str = Field(..., description="Option content")


class AptitudeQuestion(BaseModel):
    question_id: str
    category: str
    subtopic: str
    difficulty: str
    question_text: str
    options: List[MCQOption]
    correct_option: str
    explanation: str


class AptitudeClientQuestion(BaseModel):
    question_id: str
    category: str
    subtopic: str
    difficulty: str
    question_text: str
    options: List[MCQOption]


class GenerateQuizRequest(BaseModel):
    category: str = Field(default="all", description="Category: quantitative, logical, verbal, or all.")
    difficulty: str = Field(default="medium", description="Difficulty: easy, medium, hard.")
    count: int = Field(default=5, ge=1, le=20, description="Number of questions in test (1-20).")


class GenerateQuizResponse(BaseModel):
    quiz_id: str
    category: str
    category_label: str
    difficulty: str
    total_questions: int
    questions: List[AptitudeClientQuestion]


class SubmitAnswerItem(BaseModel):
    question_id: str
    selected_option: Optional[str] = None


class SubmitQuizRequest(BaseModel):
    quiz_id: Optional[str] = None
    category: str
    answers: List[SubmitAnswerItem]
    time_taken_seconds: int = Field(ge=0, description="Time spent solving quiz in seconds.")


class QuestionResultItem(BaseModel):
    question_id: str
    question_text: str
    selected_option: Optional[str]
    correct_option: str
    is_correct: bool
    explanation: str


class QuizResultResponse(BaseModel):
    attempt_id: str
    category: str
    category_label: str
    total_questions: int
    correct_count: int
    wrong_count: int
    unanswered_count: int
    score_percentage: float
    time_taken_seconds: int
    results: List[QuestionResultItem]
    timestamp: str


class AptitudeHistoryResponse(BaseModel):
    total_attempts: int
    history: List[Dict]
