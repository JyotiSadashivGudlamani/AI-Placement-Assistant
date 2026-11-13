"""
BM25 Keyword Retrieval Service.
Provides sparse keyword-based search over stored document chunks using BM25Okapi.
"""

import re
from typing import Any, Dict, List, Optional
from rank_bm25 import BM25Okapi

from backend.app.services.vector_store import VectorStoreService


class BM25Service:
    """Service providing BM25 lexical keyword retrieval over document chunks."""

    _instance: Optional["BM25Service"] = None

    def __init__(self, vector_store: Optional[VectorStoreService] = None):
        self.vector_store = vector_store or VectorStoreService()
        self.bm25: Optional[BM25Okapi] = None
        self.corpus_chunks: List[Dict[str, Any]] = []
        self._last_count: int = -1
        self._build_index()

    @classmethod
    def get_instance(cls) -> "BM25Service":
        """Singleton accessor for BM25 service."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @staticmethod
    def tokenize(text: str) -> List[str]:
        """Tokenizes text into lowercase alphanumeric tokens."""
        if not text:
            return []
        return re.findall(r"\b\w+\b", text.lower())

    def _build_index(self, force: bool = False) -> None:
        """Fetches all chunks from ChromaDB and compiles the BM25 inverted index."""
        current_count = self.vector_store.count()
        if not force and current_count == self._last_count and self.bm25 is not None:
            return

        if current_count == 0:
            self.bm25 = None
            self.corpus_chunks = []
            self._last_count = 0
            return

        # Fetch all records from ChromaDB collection
        all_records = self.vector_store.collection.get(
            include=["documents", "metadatas"],
        )

        documents = all_records.get("documents") or []
        metadatas = all_records.get("metadatas") or []
        ids = all_records.get("ids") or []

        self.corpus_chunks = [
            {
                "chunk_id": chunk_id,
                "text": doc,
                "metadata": meta,
            }
            for chunk_id, doc, meta in zip(ids, documents, metadatas)
        ]

        tokenized_corpus = [self.tokenize(c["text"]) for c in self.corpus_chunks]
        self.bm25 = BM25Okapi(tokenized_corpus)
        self._last_count = current_count

    def refresh(self) -> None:
        """Forces re-indexing of chunks from ChromaDB."""
        self._build_index(force=True)

    def search(
        self,
        query: str,
        n_results: int = 4,
        where: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Executes BM25 keyword search against indexed document chunks.
        Applies optional metadata filtering and returns ranked results.
        """
        self._build_index()

        if self.bm25 is None or not self.corpus_chunks:
            return []

        tokenized_query = self.tokenize(query)
        if not tokenized_query:
            return []

        raw_scores = self.bm25.get_scores(tokenized_query)
        max_score = max(raw_scores) if len(raw_scores) > 0 and max(raw_scores) > 0 else 1.0

        candidates = []
        for idx, score in enumerate(raw_scores):
            if score <= 0.0:
                continue

            chunk = self.corpus_chunks[idx]
            meta = chunk["metadata"]

            # Apply metadata filtering if specified
            if where:
                match = True
                for key, val in where.items():
                    if meta.get(key) != val:
                        match = False
                        break
                if not match:
                    continue

            normalized_score = round(float(score / max_score), 4)
            candidates.append(
                {
                    "chunk_id": chunk["chunk_id"],
                    "text": chunk["text"],
                    "metadata": meta,
                    "bm25_raw_score": round(float(score), 4),
                    "similarity": normalized_score,
                }
            )

        # Sort by raw score descending
        candidates.sort(key=lambda x: x["bm25_raw_score"], reverse=True)

        # Assign ranks
        results = []
        for i, item in enumerate(candidates[:n_results], start=1):
            item["rank"] = i
            results.append(item)

        return results
