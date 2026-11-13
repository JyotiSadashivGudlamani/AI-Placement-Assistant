"""
Central application configuration for AI Placement Preparation Assistant.
Supports environment variables with robust fallback defaults for local,
dockerized, and production deployment environments.
"""

import os
from pathlib import Path
from typing import List, Set

try:
    from dotenv import load_dotenv
    # Attempt loading .env from project root or backend folder
    load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent.parent / ".env")
    load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent.parent.parent / ".env")
except ImportError:
    pass


class Settings:
    """Application settings backed by environment variables."""

    # Project paths
    BACKEND_DIR: Path = Path(__file__).resolve().parent.parent.parent
    PROJECT_ROOT: Path = BACKEND_DIR.parent
    CHROMA_DB_DIR: Path = Path(
        os.getenv("CHROMA_DB_DIR", str(BACKEND_DIR / "chroma_db"))
    )

    # Vector store configuration
    DEFAULT_COLLECTION_NAME: str = os.getenv(
        "DEFAULT_COLLECTION_NAME", "placement_documents"
    )
    EMBEDDING_MODEL_NAME: str = os.getenv(
        "EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2"
    )
    EMBEDDING_DIMENSION: int = int(os.getenv("EMBEDDING_DIMENSION", "384"))
    DEFAULT_TOP_K: int = int(os.getenv("DEFAULT_TOP_K", "4"))
    MIN_SIMILARITY_THRESHOLD: float = float(
        os.getenv("MIN_SIMILARITY_THRESHOLD", "0.20")
    )

    # Chunking defaults
    DEFAULT_CHUNK_SIZE: int = int(os.getenv("DEFAULT_CHUNK_SIZE", "300"))
    DEFAULT_CHUNK_OVERLAP: int = int(os.getenv("DEFAULT_CHUNK_OVERLAP", "50"))
    CHUNK_SEPARATORS: list[str] = ["\n\n", "\n", ". ", " ", ""]

    # Ingestion constraints
    ALLOWED_EXTENSIONS: Set[str] = {".pdf", ".docx", ".txt"}
    MAX_FILE_SIZE_BYTES: int = int(
        os.getenv("MAX_FILE_SIZE_BYTES", str(15 * 1024 * 1024))
    )  # 15 MB

    # Ollama LLM Configuration
    # NOTE: In Docker on Windows host, set OLLAMA_BASE_URL to http://host.docker.internal:11434
    OLLAMA_BASE_URL: str = os.getenv(
        "OLLAMA_BASE_URL", "http://127.0.0.1:11434"
    ).rstrip("/")
    OLLAMA_MODEL_NAME: str = os.getenv("OLLAMA_MODEL_NAME", "llama3.2:3b")
    OLLAMA_TIMEOUT_SECONDS: float = float(
        os.getenv("OLLAMA_TIMEOUT_SECONDS", "120.0")
    )

    # MongoDB Configuration
    # In Docker compose, set MONGO_URI to mongodb://mongo:27017
    MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    MONGO_DB_NAME: str = os.getenv("MONGO_DB_NAME", "ai_placement_prep")

    # Security & Authentication
    JWT_SECRET_KEY: str = os.getenv(
        "JWT_SECRET_KEY",
        "ai_placement_prep_jwt_super_secret_key_change_in_prod_778899",
    )
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", str(60 * 24 * 7))
    )  # 7 days

    # API Configuration
    API_TITLE: str = os.getenv(
        "API_TITLE", "AI Placement Preparation Assistant"
    )
    API_VERSION: str = os.getenv("API_VERSION", "2.0.0")

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()

    @property
    def CORS_ORIGINS(self) -> List[str]:
        env_origins = os.getenv("CORS_ORIGINS")
        if env_origins:
            return [origin.strip() for origin in env_origins.split(",") if origin.strip()]
        return [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:8000",
            "http://127.0.0.1:8000",
            "http://localhost:8001",
            "http://127.0.0.1:8001",
            "http://localhost:80",
            "http://127.0.0.1:80",
        ]


settings = Settings()
