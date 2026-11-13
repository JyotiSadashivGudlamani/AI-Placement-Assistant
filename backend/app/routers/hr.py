"""
FastAPI router for Module 2: HR Preparation.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status

from backend.app.schemas.hr import (
    HR_CATEGORIES,
    HR_CATEGORY_LABELS,
    HRQuestionRequest,
    HRQuestionResponse,
    SaveHRDraftRequest,
    SavedHRDraftItem,
    SavedHRDraftsListResponse,
)
from backend.app.services.hr_prep import HRPrepService

router = APIRouter(prefix="/hr", tags=["Module 2: HR Interview Preparation"])


@router.get("/categories", summary="List supported HR interview categories")
def get_categories():
    """Returns all 7 HR categories and descriptions."""
    return {
        "categories": [
            {"id": cat_id, "label": HR_CATEGORY_LABELS.get(cat_id, cat_id)}
            for cat_id in HR_CATEGORIES
        ]
    }


@router.post(
    "/generate",
    response_model=HRQuestionResponse,
    summary="Generate personalized HR interview question guidance and draft answer",
)
async def generate_hr_guidance(request: HRQuestionRequest):
    """
    Generates structured HR interview guidance, STAR framework breakdown,
    and a draft answer grounded in real student background without inventing achievements.
    """
    service = HRPrepService.get_instance()
    guidance = await service.generate_hr_guidance(
        category=request.category,
        target_company=request.target_company,
        target_role=request.target_role,
        student_background=request.student_background,
    )
    return HRQuestionResponse(**guidance)


@router.post("/save", summary="Save HR draft response to MongoDB")
def save_hr_draft(request: SaveHRDraftRequest):
    """Saves personalized HR answer to student's MongoDB repository."""
    service = HRPrepService.get_instance()
    saved = service.save_draft(request.model_dump())
    return {"message": "HR draft saved successfully.", "draft": saved}


@router.get(
    "/saved",
    response_model=SavedHRDraftsListResponse,
    summary="List saved HR drafts",
)
def list_saved_drafts(category: Optional[str] = Query(default=None)):
    """Retrieves all saved HR question drafts."""
    service = HRPrepService.get_instance()
    drafts = service.list_saved_drafts(category=category)
    return SavedHRDraftsListResponse(
        total=len(drafts),
        drafts=[SavedHRDraftItem(**d) for d in drafts],
    )


@router.delete("/saved/{draft_id}", summary="Delete an HR draft")
def delete_saved_draft(draft_id: str):
    """Removes a saved HR draft from MongoDB."""
    service = HRPrepService.get_instance()
    success = service.delete_saved_draft(draft_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"HR draft '{draft_id}' not found.",
        )
    return {"message": f"HR draft '{draft_id}' deleted successfully."}
