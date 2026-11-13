"""
Pydantic schemas for Module 5: Job Description Analyser.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class SkillMatchDetails(BaseModel):
    matched_required_skills: List[str] = []
    missing_required_skills: List[str] = []
    matched_preferred_skills: List[str] = []
    missing_preferred_skills: List[str] = []
    required_match_percentage: float
    preferred_match_percentage: float
    overall_match_score: float
    score_formula: str


class JDAnalysisRequest(BaseModel):
    jd_text: str = Field(..., min_length=20, description="Raw job description text.")
    role_title: Optional[str] = Field(default=None, description="Optional job title if known.")
    company_name: Optional[str] = Field(default=None, description="Optional hiring company name.")
    resume_id: Optional[str] = Field(default=None, description="Optional resume ID from Module 4 to match against.")
    candidate_skills: Optional[List[str]] = Field(default=None, description="Optional direct list of candidate skills.")


class JDAnalysisResponse(BaseModel):
    match_id: str
    role_title: str
    company_name: Optional[str] = None
    required_skills: List[str]
    preferred_skills: List[str]
    key_responsibilities: List[str]
    skill_match: Optional[SkillMatchDetails] = None
    recommended_learning_topics: List[str]
    preparation_action_plan: List[str]
    created_at: str


class JDMatchHistoryItem(BaseModel):
    match_id: str
    role_title: str
    company_name: Optional[str] = None
    overall_match_score: Optional[float] = None
    created_at: str


class JDMatchHistoryResponse(BaseModel):
    total: int
    matches: List[JDMatchHistoryItem]
