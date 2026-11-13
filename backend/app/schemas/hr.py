"""
Pydantic schemas for Module 2: HR Preparation.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


HR_CATEGORIES = [
    "self_introduction",
    "strengths_weaknesses",
    "career_goals",
    "teamwork",
    "problem_solving",
    "why_hire_you",
    "company_motivation",
]

HR_CATEGORY_LABELS = {
    "self_introduction": "Self-Introduction (Elevator Pitch)",
    "strengths_weaknesses": "Strengths & Weaknesses",
    "career_goals": "Short & Long-Term Career Goals",
    "teamwork": "Teamwork & Conflict Resolution",
    "problem_solving": "Problem Solving & Analytical Thinking",
    "why_hire_you": "Why Should We Hire You?",
    "company_motivation": "Company-Specific Motivation",
}


class HRQuestionRequest(BaseModel):
    category: str = Field(..., description="Target HR interview category.")
    target_company: Optional[str] = Field(default=None, description="Optional target company name.")
    target_role: Optional[str] = Field(default="Software Engineer", description="Target job title.")
    student_background: Optional[str] = Field(
        default=None,
        description="Real student details: degree, technologies, college projects. Never invent achievements.",
    )


class HRQuestionResponse(BaseModel):
    draft_id: str
    category: str
    category_label: str
    question: str
    framework: str
    draft_answer: str
    sample_structure: List[str]
    dos_and_donts: List[str]
    follow_up_questions: List[str]


class SaveHRDraftRequest(BaseModel):
    draft_id: str
    category: str
    question: str
    draft_answer: str
    target_company: Optional[str] = None
    user_notes: Optional[str] = None


class SavedHRDraftItem(BaseModel):
    draft_id: str
    category: str
    question: str
    draft_answer: str
    target_company: Optional[str] = None
    user_notes: Optional[str] = None
    created_at: str


class SavedHRDraftsListResponse(BaseModel):
    total: int
    drafts: List[SavedHRDraftItem]
