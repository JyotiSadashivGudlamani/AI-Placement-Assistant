"""
Advanced RAG Pipeline Service.
Combines Vector Search, BM25, Reciprocal Rank Fusion (RRF), Cross-Encoder Reranking,
Multi-Query Expansion, and Context Compression into a unified, configurable engine.
"""

from typing import Any, Dict, List, Literal, Optional, Set
import numpy as np

from backend.app.core.config import settings
from backend.app.services.bm25 import BM25Service
from backend.app.services.query_transform import QueryTransformService
from backend.app.services.reranker import RerankerService
from backend.app.services.vector_store import VectorStoreService

RetrievalMode = Literal["basic", "vector", "bm25", "hybrid", "hybrid_rerank"]


class AdvancedRAGService:
    """Orchestrates Advanced Retrieval: Vector, BM25, Hybrid (RRF), Reranking, and Compression."""

    _instance: Optional["AdvancedRAGService"] = None

    def __init__(
        self,
        vector_store: Optional[VectorStoreService] = None,
        bm25_service: Optional[BM25Service] = None,
        reranker: Optional[RerankerService] = None,
        query_transformer: Optional[QueryTransformService] = None,
    ):
        self.vector_store = vector_store or VectorStoreService()
        self.bm25_service = bm25_service or BM25Service.get_instance()
        self.reranker = reranker or RerankerService.get_instance()
        self.query_transformer = query_transformer or QueryTransformService.get_instance()

    @classmethod
    def get_instance(cls) -> "AdvancedRAGService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # -------------------------------------------------------------
    # 1. Reciprocal Rank Fusion (RRF)
    # -------------------------------------------------------------
    @staticmethod
    def reciprocal_rank_fusion(
        ranked_lists: List[List[Dict[str, Any]]],
        k: int = 60,
        top_n: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Merges multiple ranked lists of chunks using Reciprocal Rank Fusion.
        RRF Score = Sum_i ( 1 / (k + rank_i) )
        """
        scores: Dict[str, float] = {}
        chunk_map: Dict[str, Dict[str, Any]] = {}

        for rank_list in ranked_lists:
            for rank_idx, item in enumerate(rank_list, start=1):
                chunk_id = item["chunk_id"]
                if chunk_id not in chunk_map:
                    chunk_map[chunk_id] = item

                # Calculate RRF score
                rrf_increment = 1.0 / (k + rank_idx)
                scores[chunk_id] = scores.get(chunk_id, 0.0) + rrf_increment

        # Sort by fused RRF score descending
        sorted_chunk_ids = sorted(scores.keys(), key=lambda cid: scores[cid], reverse=True)

        fused_results: List[Dict[str, Any]] = []
        max_rrf = max(scores.values()) if scores else 1.0

        for new_rank, chunk_id in enumerate(sorted_chunk_ids[:top_n], start=1):
            base_item = dict(chunk_map[chunk_id])
            base_item["rank"] = new_rank
            base_item["rrf_score"] = round(scores[chunk_id], 6)
            base_item["similarity"] = round(scores[chunk_id] / max_rrf, 4)
            fused_results.append(base_item)

        return fused_results

    # -------------------------------------------------------------
    # 2. Context Deduplication & Compression
    # -------------------------------------------------------------
    @staticmethod
    def compress_context(
        chunks: List[Dict[str, Any]],
        max_total_chars: int = 4000,
        jaccard_similarity_threshold: float = 0.85,
    ) -> List[Dict[str, Any]]:
        """
        Removes redundant chunks with high token overlap and enforces a max character budget
        to keep the prompt concise and prevent context clutter for Llama 3.2.
        """
        if not chunks:
            return []

        selected: List[Dict[str, Any]] = []
        seen_token_sets: List[Set[str]] = []
        current_chars = 0

        for chunk in chunks:
            text = chunk.get("text", "").strip()
            tokens = set(text.lower().split())

            # Check Jaccard overlap with already selected chunks
            is_duplicate = False
            for prev_tokens in seen_token_sets:
                intersection = len(tokens & prev_tokens)
                union = len(tokens | prev_tokens)
                if union > 0 and (intersection / union) >= jaccard_similarity_threshold:
                    is_duplicate = True
                    break

            if is_duplicate:
                continue

            # Check character budget
            if current_chars + len(text) > max_total_chars and len(selected) >= 1:
                break

            selected.append(chunk)
            seen_token_sets.append(tokens)
            current_chars += len(text)

        return selected

    # -------------------------------------------------------------
    # 3. Unified Search Execution
    # -------------------------------------------------------------
    async def retrieve(
        self,
        query: str,
        mode: RetrievalMode = "hybrid_rerank",
        top_k: int = 4,
        where: Optional[Dict[str, Any]] = None,
        use_multi_query: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Main retrieval entrypoint supporting:
        - 'basic' or 'vector': Standard ChromaDB semantic search
        - 'bm25': BM25 keyword search
        - 'hybrid': Reciprocal Rank Fusion of Vector + BM25
        - 'hybrid_rerank': Hybrid search with Cross-Encoder reranking
        """
        clean_query = query.strip()
        if not clean_query:
            return []

        # A. Basic / Dense Vector Search
        if mode in ("basic", "vector"):
            return self.vector_store.search(
                query=clean_query,
                n_results=top_k,
                where=where,
            )

        # B. BM25 Keyword Search
        if mode == "bm25":
            return self.bm25_service.search(
                query=clean_query,
                n_results=top_k,
                where=where,
            )

        # C. Multi-Query Expansion (if enabled)
        queries = [clean_query]
        if use_multi_query:
            queries = await self.query_transformer.generate_multi_queries(clean_query, num_queries=3)

        # D. Hybrid Retrieval (Vector + BM25 per query)
        candidate_pool_size = max(top_k * 3, 10)
        ranked_lists: List[List[Dict[str, Any]]] = []

        for q in queries:
            # 1. Vector candidates
            v_candidates = self.vector_store.search(
                query=q,
                n_results=candidate_pool_size,
                where=where,
            )
            if v_candidates:
                ranked_lists.append(v_candidates)

            # 2. BM25 candidates
            b_candidates = self.bm25_service.search(
                query=q,
                n_results=candidate_pool_size,
                where=where,
            )
            if b_candidates:
                ranked_lists.append(b_candidates)

        if not ranked_lists:
            return []

        # Fusion using Reciprocal Rank Fusion
        fused_candidates = self.reciprocal_rank_fusion(
            ranked_lists=ranked_lists,
            k=60,
            top_n=candidate_pool_size,
        )

        # E. Cross-Encoder Reranking
        if mode == "hybrid_rerank":
            reranked = self.reranker.rerank(
                query=clean_query,
                candidates=fused_candidates,
                top_k=top_k * 2,  # Rerank broader candidate set
            )
            final_chunks = self.compress_context(reranked)[:top_k]
        else:
            final_chunks = self.compress_context(fused_candidates)[:top_k]

        return final_chunks
