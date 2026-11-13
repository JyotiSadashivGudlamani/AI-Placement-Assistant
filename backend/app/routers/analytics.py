"""
FastAPI router for Phase 7 Student Preparation Analytics and Dashboard Insights.
Aggregates activity, aptitude progress, mock interview metrics, and topic recommendations.
"""

from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, status

from backend.app.core.deps import get_optional_current_user
from backend.app.db.mongo import MongoDBManager
from backend.app.schemas.user import UserProfile

router = APIRouter(prefix="/analytics", tags=["Phase 7: Student Preparation Analytics"])


@router.get(
    "/dashboard",
    summary="Get personalized student placement dashboard analytics",
)
def get_dashboard_analytics(
    current_user: Optional[UserProfile] = Depends(get_optional_current_user),
) -> Dict[str, Any]:
    """
    Returns aggregated metrics for the student dashboard:
    - Total uploaded documents
    - Total questions asked across chat & agent sessions
    - Technical preparation activity
    - Aptitude test scores & category breakdown
    - Mock interview ratings across 5 criteria
    - Recent chronological activity timeline
    - Topic-wise progress % across CS fundamentals
    - Recommended next learning topics
    """
    mongo = MongoDBManager.get_instance()
    if not mongo.is_connected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection is unavailable.",
        )

    user_id = current_user.user_id if current_user else None
    analytics = mongo.get_user_analytics(user_id=user_id)
    return analytics
