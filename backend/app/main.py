"""
FastAPI application entrypoint for AI Placement Preparation Assistant.
Mounts modular routers, sets up CORS, health probes, and application lifecycle.
"""

from contextlib import asynccontextmanager
from typing import Any, Dict
import httpx
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.core.config import settings
from backend.app.core.logger import configure_logging, get_logger
from backend.app.db.mongo import MongoDBManager
from backend.app.routers.chat import router as chat_router
from backend.app.routers.documents import router as documents_router
from backend.app.routers.technical import router as technical_router
from backend.app.routers.hr import router as hr_router
from backend.app.routers.aptitude import router as aptitude_router
from backend.app.routers.resume import router as resume_router
from backend.app.routers.jd import router as jd_router
from backend.app.routers.mock_interview import router as mock_interview_router
from backend.app.routers.agent import router as agent_router
from backend.app.routers.auth import router as auth_router
from backend.app.routers.analytics import router as analytics_router
from backend.app.services.embeddings import EmbeddingService
from backend.app.services.vector_store import VectorStoreService

# Initialize centralized logging
configure_logging(settings.LOG_LEVEL)
logger = get_logger("app.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context for startup and shutdown routines."""
    logger.info("=======================================================")
    logger.info(f"Starting {settings.API_TITLE} v{settings.API_VERSION}")
    logger.info(f"Root directory: {settings.PROJECT_ROOT}")
    logger.info(f"ChromaDB path: {settings.CHROMA_DB_DIR}")
    logger.info(f"Ollama base URL: {settings.OLLAMA_BASE_URL} (Model: {settings.OLLAMA_MODEL_NAME})")

    # Warm up / verify connections
    mongo = MongoDBManager.get_instance()
    if mongo.is_connected:
        logger.info(f"MongoDB connected: {settings.MONGO_URI} / {settings.MONGO_DB_NAME}")
    else:
        logger.warning(f"MongoDB offline or unavailable at {settings.MONGO_URI}")

    # Warm up embedding singleton
    try:
        embedding_service = EmbeddingService.get_instance()
        logger.info(f"Embedding model ready: {settings.EMBEDDING_MODEL_NAME} (Dim: {settings.EMBEDDING_DIMENSION})")
    except Exception as e:
        logger.warning(f"Embedding model warm-up warning: {e}")

    logger.info("=======================================================")
    yield
    logger.info(f"Shutting down {settings.API_TITLE}...")


app = FastAPI(
    title=settings.API_TITLE,
    description=(
        "AI-powered Placement Preparation Assistant featuring PyMuPDF ingestion, "
        "ChromaDB vector search, Ollama Llama 3.2:3b RAG answering, and MongoDB session tracking."
    ),
    version=settings.API_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount modular routers
app.include_router(auth_router)
app.include_router(analytics_router)
app.include_router(documents_router)
app.include_router(chat_router)
app.include_router(technical_router)
app.include_router(hr_router)
app.include_router(aptitude_router)
app.include_router(resume_router)
app.include_router(jd_router)
app.include_router(mock_interview_router)
app.include_router(agent_router)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request, exc: Exception):
    logger.error(f"Unhandled exception on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error occurred. Check server logs for details."},
    )


@app.get(
    "/",
    tags=["General"],
    summary="API Root Information",
)
def root() -> Dict[str, Any]:
    """Returns application title, version, documentation links, and operational status."""
    return {
        "title": settings.API_TITLE,
        "version": settings.API_VERSION,
        "status": "Running",
        "documentation": "/docs",
        "redoc": "/redoc",
        "endpoints": {
            "health": "/health",
            "auth_register": "POST /auth/register",
            "auth_login": "POST /auth/login",
            "auth_me": "GET /auth/me",
            "dashboard_analytics": "GET /analytics/dashboard",
            "upload_document": "POST /documents/upload",
            "list_documents": "GET /documents",
            "document_status": "GET /documents/{document_id}",
            "delete_document": "DELETE /documents/{document_id}",
            "chat": "POST /chat",
            "chat_sessions": "GET /chats",
            "session_history": "GET /chats/{session_id}",
            "agent_chat": "POST /agent/chat",
            "agent_sessions": "GET /agent/sessions",
            "agent_session_history": "GET /agent/session/{session_id}",
            "agent_workflow": "GET /agent/workflow",
        },
    }


@app.get(
    "/health",
    tags=["General"],
    summary="Health check probe for all subsystem dependencies",
)
async def health_check() -> JSONResponse:
    """Probes status of ChromaDB, Ollama daemon, MongoDB, and embedding models."""
    health_status: Dict[str, Any] = {
        "status": "healthy",
        "components": {},
    }

    # 1. Check ChromaDB
    try:
        vs = VectorStoreService()
        record_count = vs.count()
        health_status["components"]["chromadb"] = {
            "status": "healthy",
            "total_records": record_count,
            "collection": vs.collection_name,
        }
    except Exception as e:
        health_status["components"]["chromadb"] = {"status": "unhealthy", "error": str(e)}
        health_status["status"] = "degraded"

    # 2. Check Ollama
    try:
        async with httpx.AsyncClient(timeout=4.0) as client:
            resp = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
            if resp.status_code == 200:
                tags = resp.json().get("models", [])
                model_names = [m.get("name", "") for m in tags]
                has_target_model = any(settings.OLLAMA_MODEL_NAME in m for m in model_names)
                health_status["components"]["ollama"] = {
                    "status": "healthy",
                    "target_model": settings.OLLAMA_MODEL_NAME,
                    "target_model_installed": has_target_model,
                    "available_models": model_names,
                }
            else:
                health_status["components"]["ollama"] = {
                    "status": "unhealthy",
                    "http_code": resp.status_code,
                }
                health_status["status"] = "degraded"
    except Exception as e:
        health_status["components"]["ollama"] = {"status": "unhealthy", "error": str(e)}
        health_status["status"] = "degraded"

    # 3. Check MongoDB
    mongo = MongoDBManager.get_instance()
    if mongo.is_connected:
        health_status["components"]["mongodb"] = {
            "status": "healthy",
            "database": settings.MONGO_DB_NAME,
        }
    else:
        health_status["components"]["mongodb"] = {
            "status": "unhealthy",
            "error": "Cannot ping MongoDB",
        }
        health_status["status"] = "degraded"

    # 4. Check Embedding Model
    try:
        emb_service = EmbeddingService.get_instance()
        health_status["components"]["embeddings"] = {
            "status": "healthy",
            "model": emb_service.model_name,
            "dimension": emb_service.expected_dimension,
        }
    except Exception as e:
        health_status["components"]["embeddings"] = {"status": "unhealthy", "error": str(e)}
        health_status["status"] = "degraded"

    http_code = (
        status.HTTP_200_OK if health_status["status"] == "healthy" else status.HTTP_207_MULTI_STATUS
    )
    return JSONResponse(status_code=http_code, content=health_status)
