"""
FastAPI dependency injectors for Phase 7 Authentication and User Validation.
Validates JWT Bearer tokens and resolves authenticated user context.
"""

from typing import Optional
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.app.core.security import decode_access_token
from backend.app.db.mongo import MongoDBManager
from backend.app.schemas.user import UserProfile

# Standard HTTP Bearer scheme
security_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
) -> UserProfile:
    """
    Strict dependency enforcing valid JWT Bearer authentication.
    Raises 401 UNAUTHORIZED if token is missing, invalid, or expired.
    """
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please provide a valid Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed token claims.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    mongo = MongoDBManager.get_instance()
    user_record = mongo.get_user_by_id(user_id)
    if not user_record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account no longer exists.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user_record.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated.",
        )

    return UserProfile(
        user_id=user_record["user_id"],
        email=user_record["email"],
        full_name=user_record["full_name"],
        created_at=user_record.get("created_at", ""),
        is_active=user_record.get("is_active", True),
    )


async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
) -> Optional[UserProfile]:
    """
    Permissive dependency returning authenticated user if token is valid,
    or None if token is omitted. Preserves compatibility for guest sessions and testing.
    """
    if credentials is None or not credentials.credentials:
        return None

    try:
        payload = decode_access_token(credentials.credentials)
        if not payload or not payload.get("sub"):
            return None

        mongo = MongoDBManager.get_instance()
        user_record = mongo.get_user_by_id(payload["sub"])
        if not user_record or not user_record.get("is_active", True):
            return None

        return UserProfile(
            user_id=user_record["user_id"],
            email=user_record["email"],
            full_name=user_record["full_name"],
            created_at=user_record.get("created_at", ""),
            is_active=user_record.get("is_active", True),
        )
    except Exception:
        return None
