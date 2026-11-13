"""
Pydantic schemas for Module 6: Mock Interview.
Evaluates student responses across 5 core criteria:
Correctness, Relevance, Completeness, Clarity, and Communication.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class EvaluationScores(BaseModel):
    correctness: int = Field(..., ge=1, le=10, description="Technical/factual accuracy (1-10).")
    relevance: int = Field(..., ge=1, le=10, description="Relevance to the specific question asked (1-10).")
    completeness: int = Field(..., ge=1, le=10, description="Thoroughness of explanation & edge cases (1-10).")
    clarity: int = Field(..., ge=1, le=10, description="Precision of articulation and structure (1-10).")
    communication: int = Field(..., ge=1, le=10, description="Professional interview tone and delivery (1-10).")
    overall_score: float = Field(..., ge=1.0, le=10.0, description="Mean overall score (1-10).")


class InterviewTurn(BaseModel):
    turn_number: int
    question: str
    student_answer: Optional[str] = None
    feedback: Optional[str] = None
    improved_answer: Optional[str] = None
    scores: Optional[EvaluationScores] = None
    timestamp: Optional[str] = None


class StartInterviewRequest(BaseModel):
    interview_type: str = Field(default="technical", description="technical or hr")
    topic: str = Field(default="Java", description="Specific technical topic or HR competency.")
    difficulty: str = Field(default="medium", description="easy, medium, hard")
    total_questions: int = Field(default=3, ge=1, le=5, description="Number of questions in mock session (1-5).")


class StartInterviewResponse(BaseModel):
    session_id: str
    interview_type: str
    topic: str
    difficulty: str
    total_questions: int
    current_question_number: int
    question: str
    status: str


class SubmitAnswerRequest(BaseModel):
    student_answer: str = Field(..., min_length=2, description="Student's verbal or written answer.")


class SubmitAnswerResponse(BaseModel):
    session_id: str
    turn_number: int
    evaluated_question: str
    student_answer: str
    scores: EvaluationScores
    feedback: str
    improved_answer: str
    is_completed: bool
    next_question: Optional[str] = None
    next_question_number: Optional[int] = None
    final_summary: Optional[Dict[str, Any]] = None


class MockInterviewSessionDetail(BaseModel):
    session_id: str
    interview_type: str
    topic: str
    difficulty: str
    status: str
    total_questions: int
    completed_questions: int
    average_score: Optional[float] = None
    turns: List[InterviewTurn]
    final_summary: Optional[Dict[str, Any]] = None
    created_at: str
    updated_at: str


class MockInterviewHistoryItem(BaseModel):
    session_id: str
    interview_type: str
    topic: str
    difficulty: str
    status: str
    total_questions: int
    completed_questions: int
    average_score: Optional[float] = None
    created_at: str


class MockInterviewHistoryResponse(BaseModel):
    total: int
    sessions: List[MockInterviewHistoryItem]
