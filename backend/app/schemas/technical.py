"""
Pydantic schemas for Module 1: Technical Interview Preparation.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


TECHNICAL_TOPICS = [
    "Java",
    "Python",
    "C and C++",
    "OOP",
    "DSA",
    "DBMS",
    "SQL",
    "Operating Systems",
    "Computer Networks",
    "AI and ML",
    "LLM and RAG",
]

DIFFICULTY_LEVELS = ["easy", "medium", "hard"]


class TechnicalQuestionRequest(BaseModel):
    topic: str = Field(..., description="Target technical topic.")
    difficulty: str = Field(default="medium", description="Difficulty level: easy, medium, hard.")
    subtopic: Optional[str] = Field(default=None, description="Optional specific subtopic.")
    include_code: bool = Field(default=True, description="Whether code examples are relevant.")


class TechnicalQuestionResponse(BaseModel):
    question_id: str
    topic: str
    subtopic: str
    difficulty: str
    question: str
    answer: str
    explanation: str
    code_example: Optional[str] = None
    code_language: Optional[str] = None
    follow_up_questions: List[str] = []
    key_takeaways: List[str] = []


class SaveQuestionRequest(BaseModel):
    question_id: str
    topic: str
    difficulty: str
    question: str
    answer: str
    explanation: str
    code_example: Optional[str] = None
    follow_up_questions: List[str] = []
    notes: Optional[str] = None


class SavedQuestionItem(BaseModel):
    question_id: str
    topic: str
    difficulty: str
    question: str
    answer: str
    explanation: str
    code_example: Optional[str] = None
    follow_up_questions: List[str] = []
    notes: Optional[str] = None
    created_at: str


class SavedQuestionsListResponse(BaseModel):
    total: int
    questions: List[SavedQuestionItem]
