"""
Cross-Encoder Reranking Service.
Re-ranks candidate passages using a cross-encoder model (ms-marco-MiniLM-L-6-v2)
for deep token-level cross-attention between queries and retrieved chunks.
"""

from typing import Any, Dict, List, Optional
import numpy as np
from sentence_transformers import CrossEncoder


class RerankerService:
    """Service to rerank retrieved candidate passages using a fine-tuned Cross-Encoder."""

    _instance: Optional["RerankerService"] = None
    _model: Optional[CrossEncoder] = None

    DEFAULT_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or self.DEFAULT_MODEL
        self._load_model()

    def _load_model(self) -> None:
        """Loads CrossEncoder model singleton."""
        if RerankerService._model is None:
            RerankerService._model = CrossEncoder(self.model_name)
        self.model = RerankerService._model

    @classmethod
    def get_instance(cls) -> "RerankerService":
        """Singleton accessor for Reranker service."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @staticmethod
    def _sigmoid(x: float) -> float:
        """Converts raw logit score to normalized 0-1 probability."""
        return float(1.0 / (1.0 + np.exp(-x)))

    def rerank(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        top_k: int = 4,
    ) -> List[Dict[str, Any]]:
        """
        Reranks a list of candidate chunks against the user query.
        Returns top_k chunks sorted by fine-grained cross-attention relevance score.
        """
        if not candidates:
            return []

        if len(candidates) == 1:
            candidates[0]["rerank_score"] = 1.0
            candidates[0]["rank"] = 1
            return candidates

        # Prepare (query, passage) pairs
        pairs = [(query, c.get("text", "")) for c in candidates]

        raw_scores = self.model.predict(pairs, show_progress_bar=False)

        # Attach scores and original positions
        scored_candidates = []
        for i, (cand, score) in enumerate(zip(candidates, raw_scores), start=1):
            cand_copy = dict(cand)
            cand_copy["original_rank"] = cand.get("rank", i)
            cand_copy["rerank_raw_score"] = round(float(score), 4)
            cand_copy["rerank_score"] = round(self._sigmoid(float(score)), 4)
            scored_candidates.append(cand_copy)

        # Sort descending by cross-encoder score
        scored_candidates.sort(key=lambda x: x["rerank_raw_score"], reverse=True)

        # Assign updated ranks
        reranked_results = []
        for new_rank, item in enumerate(scored_candidates[:top_k], start=1):
            item["rank"] = new_rank
            # Update similarity metric to rerank score for uniform downstream display
            item["similarity"] = item["rerank_score"]
            reranked_results.append(item)

        return reranked_results
