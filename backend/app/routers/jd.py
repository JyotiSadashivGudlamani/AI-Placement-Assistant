"""
FastAPI router for Module 5: Job Description Analyser.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, status

from backend.app.schemas.jd import (
    JDAnalysisRequest,
    JDAnalysisResponse,
    JDMatchHistoryItem,
    JDMatchHistoryResponse,
)
from backend.app.services.jd_analyzer import JDAnalyzerService

router = APIRouter(prefix="/jd", tags=["Module 5: Job Description Analyser"])


@router.post(
    "/analyze",
    response_model=JDAnalysisResponse,
    summary="Analyze Job Description and calculate transparent resume skill match",
)
async def analyze_job_description(request: JDAnalysisRequest):
    """
    Extracts required skills, preferred skills, and core responsibilities from a JD.
    If a resume_id or candidate skills list is provided, computes a transparent
    skill match score, lists critical missing skills, and outlines a targeted learning plan.
    """
    service = JDAnalyzerService.get_instance()
    result = await service.analyze_job_description(
        jd_text=request.jd_text,
        role_title=request.role_title,
        company_name=request.company_name,
        resume_id=request.resume_id,
        candidate_skills=request.candidate_skills,
    )
    return JDAnalysisResponse(**result)


@router.get(
    "/history",
    response_model=JDMatchHistoryResponse,
    summary="List past JD analyses and skill-match records",
)
def get_match_history(limit: int = Query(default=20, ge=1, le=50)):
    """Retrieves recent JD analysis reports from MongoDB."""
    service = JDAnalyzerService.get_instance()
    matches = service.get_match_history(limit=limit)
    items = [
        JDMatchHistoryItem(
            match_id=m["match_id"],
            role_title=m.get("role_title", "Software Engineer"),
            company_name=m.get("company_name"),
            overall_match_score=m.get("skill_match", {}).get("overall_match_score") if m.get("skill_match") else None,
            created_at=m.get("created_at", ""),
        )
        for m in matches
    ]
    return JDMatchHistoryResponse(total=len(items), matches=items)
