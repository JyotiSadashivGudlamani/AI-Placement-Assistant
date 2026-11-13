"""
FastAPI router for Module 4: Resume Analyser.
"""

from pathlib import Path
import shutil
import tempfile
from typing import List
from fastapi import APIRouter, File, HTTPException, UploadFile, status

from backend.app.schemas.resume import (
    ResumeAnalysisResponse,
    ResumeListResponse,
    ResumeSummaryItem,
)
from backend.app.services.resume_analyzer import ResumeAnalyzerService

router = APIRouter(prefix="/resume", tags=["Module 4: Resume Analyser"])


@router.post(
    "/analyze",
    response_model=ResumeAnalysisResponse,
    summary="Upload and analyze a resume (PDF or DOCX)",
)
async def analyze_resume(file: UploadFile = File(...)):
    """
    Parses an uploaded PDF or DOCX resume.
    Extracts contact info, technical skills, education, and projects without hallucinating.
    Audits strengths, identifies missing information, and generates actionable improvement suggestions.
    """
    filename = file.filename or "resume.pdf"
    suffix = Path(filename).suffix.lower()

    if suffix not in [".pdf", ".docx"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{suffix}'. Only .pdf and .docx are supported for resume analysis.",
        )

    # Save to temporary file for parsing
    temp_dir = Path(tempfile.mkdtemp(prefix="resume_upload_"))
    temp_file = temp_dir / filename

    try:
        with open(temp_file, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        service = ResumeAnalyzerService.get_instance()
        result = await service.analyze_file(file_path=temp_file, filename=filename)
        return ResumeAnalysisResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze resume: {str(e)}",
        )
    finally:
        # Cleanup temporary upload folder
        shutil.rmtree(temp_dir, ignore_errors=True)


@router.get(
    "/{resume_id}",
    response_model=ResumeAnalysisResponse,
    summary="Get previously analyzed resume profile by ID",
)
def get_resume(resume_id: str):
    """Retrieves full parsed resume profile from MongoDB."""
    service = ResumeAnalyzerService.get_instance()
    profile = service.get_resume(resume_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resume '{resume_id}' not found.",
        )
    return ResumeAnalysisResponse(**profile)


@router.get(
    "s/all",
    response_model=ResumeListResponse,
    summary="List all analyzed resume profiles",
)
def list_resumes():
    """Lists summary of all previously uploaded and analyzed resumes."""
    service = ResumeAnalyzerService.get_instance()
    resumes = service.list_resumes()
    items = [
        ResumeSummaryItem(
            resume_id=r["resume_id"],
            filename=r.get("filename", "resume"),
            uploaded_at=r.get("uploaded_at", ""),
            skills_count=len(r.get("skills", {}).get("all_skills", [])),
            education_count=len(r.get("education", [])),
            projects_count=len(r.get("projects", [])),
        )
        for r in resumes
    ]
    return ResumeListResponse(total=len(items), resumes=items)
