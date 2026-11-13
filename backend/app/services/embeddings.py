"""
Embedding generation service utilizing Sentence Transformers (all-MiniLM-L6-v2).
Provides caching, batch processing, and embedding dimension validation.
"""

from typing import List, Optional
import numpy as np
from sentence_transformers import SentenceTransformer

from backend.app.core.config import settings
from backend.app.services.chunking import DocumentChunk


class EmbeddingDimensionMismatchError(ValueError):
    """Raised when generated embedding dimension doesn't match expected size."""
    pass


class EmbeddingService:
    """Service to generate dense vector embeddings from text chunks and queries."""

    _instance: Optional["EmbeddingService"] = None
    _model: Optional[SentenceTransformer] = None

    def __init__(
        self,
        model_name: Optional[str] = None,
        expected_dimension: Optional[int] = None,
    ):
        self.model_name = model_name or settings.EMBEDDING_MODEL_NAME
        self.expected_dimension = expected_dimension or settings.EMBEDDING_DIMENSION
        self._load_model()

    def _load_model(self) -> None:
        """Loads the SentenceTransformer model if not already loaded."""
        if EmbeddingService._model is None:
            EmbeddingService._model = SentenceTransformer(self.model_name)
        self.model = EmbeddingService._model

    @classmethod
    def get_instance(cls) -> "EmbeddingService":
        """Singleton accessor to reuse the loaded model across the application."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def embed_query(self, query: str) -> List[float]:
        """Generates an embedding vector for a single query string."""
        if not query or not query.strip():
            raise ValueError("Query string cannot be empty.")

        embedding = self.model.encode(
            query.strip(),
            convert_to_numpy=True,
            show_progress_bar=False,
        )

        vector = embedding.tolist()
        self._validate_dimension(vector)
        return vector

    def embed_texts(
        self,
        texts: List[str],
        batch_size: int = 32,
    ) -> List[List[float]]:
        """Generates embedding vectors for a batch of text strings."""
        if not texts:
            return []

        cleaned_texts = [t.strip() for t in texts]

        embeddings = self.model.encode(
            cleaned_texts,
            batch_size=batch_size,
            convert_to_numpy=True,
            show_progress_bar=False,
        )

        vectors: List[List[float]] = embeddings.tolist()

        for vec in vectors:
            self._validate_dimension(vec)

        return vectors

    def embed_chunks(
        self,
        chunks: List[DocumentChunk],
        batch_size: int = 32,
    ) -> List[List[float]]:
        """Generates embeddings for a list of DocumentChunk objects."""
        if not chunks:
            return []

        texts = [chunk.text for chunk in chunks]
        return self.embed_texts(texts=texts, batch_size=batch_size)

    def _validate_dimension(self, vector: List[float]) -> None:
        """Validates that vector dimension matches expected configuration."""
        actual_dim = len(vector)
        if actual_dim != self.expected_dimension:
            raise EmbeddingDimensionMismatchError(
                f"Embedding dimension mismatch: expected {self.expected_dimension}, "
                f"got {actual_dim}."
            )
