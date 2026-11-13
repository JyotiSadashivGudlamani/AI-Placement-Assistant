"""
FastAPI router for Phase 7 User Authentication and Registration.
Implements bcrypt password hashing, JWT issue/validation, and profile retrieval.
"""

from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, status

from backend.app.core.config import settings
from backend.app.core.deps import get_current_user
from backend.app.core.security import hash_password, verify_password, create_access_token
from backend.app.db.mongo import MongoDBManager
from backend.app.schemas.user import (
    TokenResponse,
    UserLoginRequest,
    UserProfile,
    UserRegisterRequest,
)

router = APIRouter(prefix="/auth", tags=["Phase 7: User Management & Authentication"])


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new student account",
)
def register_user(request: UserRegisterRequest):
    """
    Registers a new student account with bcrypt password hashing.
    Generates a JWT access token upon successful registration.
    """
    mongo = MongoDBManager.get_instance()
    if not mongo.is_connected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection is unavailable.",
        )

    clean_email = request.email.strip().lower()

    # Check if user already exists
    existing = mongo.get_user_by_email(clean_email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists.",
        )

    # Securely hash password
    hashed_pwd = hash_password(request.password)
    user_id = f"user_{uuid4().hex[:12]}"

    created_user = mongo.create_user(
        user_id=user_id,
        email=clean_email,
        full_name=request.full_name.strip(),
        hashed_password=hashed_pwd,
    )

    # Issue JWT token
    token = create_access_token({
        "sub": user_id,
        "email": clean_email,
        "name": request.full_name.strip(),
    })

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        user=UserProfile(**created_user),
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate student and obtain JWT Bearer token",
)
def login_user(request: UserLoginRequest):
    """
    Authenticates student credentials via bcrypt hash comparison.
    Issues cryptographically signed JWT token on success.
    """
    mongo = MongoDBManager.get_instance()
    if not mongo.is_connected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection is unavailable.",
        )

    clean_email = request.email.strip().lower()
    user_doc = mongo.get_user_by_email(clean_email)
    if not user_doc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify bcrypt hash
    if not verify_password(request.password, user_doc.get("hashed_password", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user_doc.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated.",
        )

    # Issue token
    token = create_access_token({
        "sub": user_doc["user_id"],
        "email": clean_email,
        "name": user_doc.get("full_name", ""),
    })

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        user=UserProfile(
            user_id=user_doc["user_id"],
            email=user_doc["email"],
            full_name=user_doc["full_name"],
            created_at=user_doc.get("created_at", ""),
            is_active=user_doc.get("is_active", True),
        ),
    )


@router.get(
    "/me",
    response_model=UserProfile,
    summary="Get authenticated student profile",
)
def get_me(current_user: UserProfile = Depends(get_current_user)):
    """Protected endpoint validating JWT token and returning user profile."""
    return current_user


@router.post(
    "/logout",
    summary="Logout authenticated student session",
)
def logout(current_user: UserProfile = Depends(get_current_user)):
    """Confirmation endpoint for client-side token discarding."""
    return {
        "status": "success",
        "message": f"User {current_user.email} logged out successfully.",
    }
