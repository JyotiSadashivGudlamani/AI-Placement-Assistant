"""
Pydantic schemas for document ingestion and management APIs.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class DocumentItem(BaseModel):
    document_id: str
    filename: str
    file_type: str
    file_size_bytes: int
    total_pages: int
    total_chunks: int
    category: str
    status: str
    uploaded_at: str


class DocumentUploadResponse(BaseModel):
    message: str = "Document successfully processed and indexed."
    document_id: str
    filename: str
    file_type: str
    file_size_bytes: int
    total_pages: int
    total_chunks: int
    category: str
    status: str = "ready"


class DocumentListResponse(BaseModel):
    total: int
    documents: List[DocumentItem]


class DocumentDetailResponse(BaseModel):
    document: DocumentItem
    chunks_count: int
    message: str = "Document details retrieved successfully."


class DocumentDeleteResponse(BaseModel):
    document_id: str
    message: str
    deleted_chunks: int
