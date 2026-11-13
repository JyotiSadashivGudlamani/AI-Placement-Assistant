"""
Recursive text chunking service for documents.
Maintains page numbers, chunk sequence indices, and stable chunk IDs.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from langchain_text_splitters import RecursiveCharacterTextSplitter

from backend.app.core.config import settings
from backend.app.services.document_loader import LoadedDocument


@dataclass
class DocumentChunk:
    """Represents an individual text chunk with associated document metadata."""
    chunk_id: str
    document_id: str
    text: str
    chunk_index: int
    page_number: int
    filename: str
    file_type: str
    category: str
    metadata: Dict[str, Any]


class TextChunker:
    """Service to recursively split documents into overlapping chunks."""

    def __init__(
        self,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
        separators: Optional[List[str]] = None,
    ):
        self.chunk_size = chunk_size or settings.DEFAULT_CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.DEFAULT_CHUNK_OVERLAP
        self.separators = separators or settings.CHUNK_SEPARATORS

        if self.chunk_overlap >= self.chunk_size:
            raise ValueError(
                f"chunk_overlap ({self.chunk_overlap}) must be strictly less than "
                f"chunk_size ({self.chunk_size})."
            )

        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=self.separators,
        )

    def chunk_document(self, document: LoadedDocument) -> List[DocumentChunk]:
        """Splits an ingested document into chunks while preserving page numbers."""
        chunks: List[DocumentChunk] = []
        global_chunk_idx = 0

        for page in document.pages:
            page_text = page.text.strip()
            if not page_text:
                continue

            page_chunks = self.splitter.split_text(page_text)

            for page_chunk_idx, chunk_text in enumerate(page_chunks):
                clean_text = chunk_text.strip()
                if not clean_text:
                    continue

                chunk_id = f"{document.document_id}_p{page.page_number}_c{page_chunk_idx + 1}"

                chunk_metadata = {
                    "document_id": document.document_id,
                    "filename": document.filename,
                    "file_type": document.file_type,
                    "category": document.category,
                    "page_number": page.page_number,
                    "chunk_id": chunk_id,
                    "chunk_index": global_chunk_idx,
                    "char_count": len(clean_text),
                }

                chunks.append(
                    DocumentChunk(
                        chunk_id=chunk_id,
                        document_id=document.document_id,
                        text=clean_text,
                        chunk_index=global_chunk_idx,
                        page_number=page.page_number,
                        filename=document.filename,
                        file_type=document.file_type,
                        category=document.category,
                        metadata=chunk_metadata,
                    )
                )
                global_chunk_idx += 1

        return chunks

    def chunk_text(
        self,
        text: str,
        document_id: str = "doc_custom",
        filename: str = "raw_text.txt",
        file_type: str = "txt",
        category: str = "custom",
        page_number: int = 1,
    ) -> List[DocumentChunk]:
        """Splits raw text string into chunks."""
        raw_chunks = self.splitter.split_text(text)
        chunks: List[DocumentChunk] = []

        for idx, chunk_text in enumerate(raw_chunks):
            clean_text = chunk_text.strip()
            if not clean_text:
                continue

            chunk_id = f"{document_id}_p{page_number}_c{idx + 1}"
            metadata = {
                "document_id": document_id,
                "filename": filename,
                "file_type": file_type,
                "category": category,
                "page_number": page_number,
                "chunk_id": chunk_id,
                "chunk_index": idx,
                "char_count": len(clean_text),
            }

            chunks.append(
                DocumentChunk(
                    chunk_id=chunk_id,
                    document_id=document_id,
                    text=clean_text,
                    chunk_index=idx,
                    page_number=page_number,
                    filename=filename,
                    file_type=file_type,
                    category=category,
                    metadata=metadata,
                )
            )

        return chunks
