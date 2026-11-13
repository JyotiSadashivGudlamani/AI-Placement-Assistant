"""
Vector store service integrating with ChromaDB.
Provides chunk storage, metadata indexing, duplicate prevention, and deletion.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import chromadb

from backend.app.core.config import settings
from backend.app.services.chunking import DocumentChunk, TextChunker
from backend.app.services.document_loader import LoadedDocument
from backend.app.services.embeddings import EmbeddingService


class VectorStoreService:
    """Manages document vectors, metadata, semantic search, and lifecycle in ChromaDB."""

    def __init__(
        self,
        chroma_db_dir: Optional[Union[str, Path]] = None,
        collection_name: Optional[str] = None,
        embedding_service: Optional[EmbeddingService] = None,
    ):
        self.chroma_db_dir = Path(chroma_db_dir or settings.CHROMA_DB_DIR)
        self.chroma_db_dir.mkdir(parents=True, exist_ok=True)
        self.collection_name = collection_name or settings.DEFAULT_COLLECTION_NAME
        self.embedding_service = embedding_service or EmbeddingService.get_instance()

        # Connect to ChromaDB persistent storage
        self.client = chromadb.PersistentClient(path=str(self.chroma_db_dir))
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def count(self) -> int:
        """Returns the total number of chunks in the collection."""
        return self.collection.count()

    def store_chunks(
        self,
        chunks: List[DocumentChunk],
        embeddings: Optional[List[List[float]]] = None,
    ) -> int:
        """
        Stores chunks in ChromaDB with metadata.
        Avoids duplicates by cleaning out existing chunks for the same document_id.
        """
        if not chunks:
            return 0

        # Group chunks by document_id and clean up previous records to prevent duplicates
        doc_ids = list({c.document_id for c in chunks})
        for doc_id in doc_ids:
            self.delete_document(doc_id)

        # Generate embeddings if not pre-computed
        if embeddings is None:
            embeddings = self.embedding_service.embed_chunks(chunks)

        if len(embeddings) != len(chunks):
            raise ValueError(
                f"Embeddings count ({len(embeddings)}) does not match chunks count ({len(chunks)})."
            )

        ids = [chunk.chunk_id for chunk in chunks]
        documents = [chunk.text for chunk in chunks]
        metadatas = [chunk.metadata for chunk in chunks]

        self.collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
        )

        return len(chunks)

    def store_document(
        self,
        document: LoadedDocument,
        chunker: Optional[TextChunker] = None,
    ) -> int:
        """
        End-to-end convenience method:
        Chunks document, generates embeddings, and saves to ChromaDB.
        """
        active_chunker = chunker or TextChunker()
        chunks = active_chunker.chunk_document(document)

        if not chunks:
            return 0

        embeddings = self.embedding_service.embed_chunks(chunks)
        return self.store_chunks(chunks=chunks, embeddings=embeddings)

    def delete_document(self, document_id: str) -> int:
        """Deletes all chunks associated with a specific document_id."""
        existing = self.collection.get(
            where={"document_id": document_id},
            include=["metadatas"],
        )

        ids_to_delete = existing.get("ids", [])
        if ids_to_delete:
            self.collection.delete(ids=ids_to_delete)

        return len(ids_to_delete)

    def delete_by_filename(self, filename: str) -> int:
        """Deletes all chunks associated with a specific filename."""
        existing = self.collection.get(
            where={"filename": filename},
            include=["metadatas"],
        )

        ids_to_delete = existing.get("ids", [])
        if ids_to_delete:
            self.collection.delete(ids=ids_to_delete)

        return len(ids_to_delete)

    def get_document_chunks(self, document_id: str) -> List[Dict[str, Any]]:
        """Retrieves all chunks belonging to a document, sorted by chunk_index."""
        results = self.collection.get(
            where={"document_id": document_id},
            include=["documents", "metadatas"],
        )

        documents = results.get("documents") or []
        metadatas = results.get("metadatas") or []
        ids = results.get("ids") or []

        items = [
            {
                "chunk_id": chunk_id,
                "text": doc,
                "metadata": meta,
                "chunk_index": meta.get("chunk_index", 0),
            }
            for chunk_id, doc, meta in zip(ids, documents, metadatas)
        ]

        items.sort(key=lambda x: x["chunk_index"])
        return items

    def search(
        self,
        query: str,
        n_results: int = 4,
        where: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Performs semantic similarity search over stored document chunks.
        Returns ranked results with cosine similarity score.
        """
        total_items = self.count()
        if total_items == 0:
            return []

        limit = min(n_results, total_items)
        query_vector = self.embedding_service.embed_query(query)

        query_params: Dict[str, Any] = {
            "query_embeddings": [query_vector],
            "n_results": limit,
            "include": ["documents", "metadatas", "distances"],
        }
        if where:
            query_params["where"] = where

        results = self.collection.query(**query_params)

        formatted_results: List[Dict[str, Any]] = []
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]
        ids = results.get("ids", [[]])[0]

        for i, (chunk_id, doc, meta, dist) in enumerate(
            zip(ids, documents, metadatas, distances)
        ):
            # Cosine distance to similarity: similarity = 1 - distance
            similarity = round(max(0.0, 1.0 - float(dist)), 4)
            formatted_results.append(
                {
                    "rank": i + 1,
                    "chunk_id": chunk_id,
                    "text": doc,
                    "similarity": similarity,
                    "distance": round(float(dist), 4),
                    "metadata": meta,
                }
            )

        return formatted_results

    def reset_collection(self) -> None:
        """Deletes and recreates the current collection (primarily for testing)."""
        self.client.delete_collection(name=self.collection_name)
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )
