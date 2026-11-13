"""
Documents router handling upload, listing, status inspection, and deletion.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from backend.app.core.deps import get_optional_current_user
from backend.app.db.mongo import MongoDBManager
from backend.app.schemas.document import (
    DocumentDeleteResponse,
    DocumentDetailResponse,
    DocumentItem,
    DocumentListResponse,
    DocumentUploadResponse,
)
from backend.app.schemas.user import UserProfile
from backend.app.services.chunking import TextChunker
from backend.app.services.document_loader import (
    DocumentLoader,
    DocumentLoaderError,
    EmptyDocumentError,
    FileTooLargeError,
    UnsupportedFileTypeError,
)
from backend.app.services.vector_store import VectorStoreService

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and ingest a placement preparation document (PDF, DOCX, TXT)",
)
async def upload_document(
    file: UploadFile = File(..., description="PDF, DOCX, or TXT file to process and index"),
    category: str = Form("placement", description="Category of the document (e.g. 'placement', 'resume', 'java')"),
    user_id: Optional[str] = Form(None, description="Optional explicit user owner"),
    current_user: Optional[UserProfile] = Depends(get_optional_current_user),
):
    """
    Ingests a document:
    1. Validates extension, size, and readable content.
    2. Extracts text (preserving page numbers for PDFs and extracting tables for DOCX).
    3. Splits into recursive overlapping chunks.
    4. Generates dense 384-dim embeddings with all-MiniLM-L6-v2.
    5. Stores vectors in ChromaDB (preventing duplicates).
    6. Registers document metadata in MongoDB.
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No filename provided in upload.",
        )

    loader = DocumentLoader()
    chunker = TextChunker()
    vector_store = VectorStoreService()
    mongo = MongoDBManager.get_instance()

    try:
        file_bytes = await file.read()
        loaded_doc = loader.load_from_bytes(
            file_bytes=file_bytes,
            filename=file.filename,
            category=category,
        )

        chunks = chunker.chunk_document(loaded_doc)
        if not chunks:
            raise EmptyDocumentError(f"No chunks could be extracted from '{file.filename}'.")

        stored_chunks = vector_store.store_chunks(chunks)

        # Refresh BM25 index with newly added document chunks
        from backend.app.services.bm25 import BM25Service
        BM25Service.get_instance().refresh()

        # Register metadata in MongoDB with user ownership
        if mongo.is_connected:
            owner_id = current_user.user_id if current_user else user_id
            mongo.register_document(
                document_id=loaded_doc.document_id,
                filename=loaded_doc.filename,
                file_type=loaded_doc.file_type,
                file_size_bytes=loaded_doc.file_size_bytes,
                total_pages=loaded_doc.total_pages,
                total_chunks=stored_chunks,
                category=loaded_doc.category,
                status="ready",
                content_hash=loaded_doc.content_hash,
                user_id=owner_id,
            )

        return DocumentUploadResponse(
            message=f"Document '{file.filename}' successfully processed and indexed.",
            document_id=loaded_doc.document_id,
            filename=loaded_doc.filename,
            file_type=loaded_doc.file_type,
            file_size_bytes=loaded_doc.file_size_bytes,
            total_pages=loaded_doc.total_pages,
            total_chunks=stored_chunks,
            category=loaded_doc.category,
            status="ready",
        )

    except UnsupportedFileTypeError as err:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail=str(err))
    except (EmptyDocumentError, FileTooLargeError) as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))
    except DocumentLoaderError as err:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(err))
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document ingestion failed: {str(err)}",
        )


@router.get(
    "",
    response_model=DocumentListResponse,
    summary="List all indexed documents",
)
def list_documents(
    category: Optional[str] = None,
    current_user: Optional[UserProfile] = Depends(get_optional_current_user),
):
    """Retrieves list of documents, filtered to current user if authenticated."""
    mongo = MongoDBManager.get_instance()
    if mongo.is_connected:
        user_id = current_user.user_id if current_user else None
        docs = mongo.list_documents(category=category, user_id=user_id)
        items = [DocumentItem(**d) for d in docs]
        return DocumentListResponse(total=len(items), documents=items)

    # Fallback to vector store chunks if MongoDB is offline
    vector_store = VectorStoreService()
    count = vector_store.count()
    return DocumentListResponse(total=0, documents=[])


@router.get(
    "/{document_id}",
    response_model=DocumentDetailResponse,
    summary="Get document details and processing status",
)
def get_document_status(
    document_id: str,
    current_user: Optional[UserProfile] = Depends(get_optional_current_user),
):
    """Retrieves document processing status and verifies user access permission."""
    mongo = MongoDBManager.get_instance()
    vector_store = VectorStoreService()

    doc_data = None
    if mongo.is_connected:
        doc_data = mongo.get_document(document_id)
        if doc_data and current_user:
            owner = doc_data.get("user_id")
            if owner and owner != current_user.user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied. You do not have permission to view this document.",
                )

    chunks = vector_store.get_document_chunks(document_id)

    if not doc_data and not chunks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{document_id}' not found in vector store or registry.",
        )

    if not doc_data:
        first_chunk_meta = chunks[0]["metadata"]
        doc_data = {
            "document_id": document_id,
            "filename": first_chunk_meta.get("filename", "unknown"),
            "file_type": first_chunk_meta.get("file_type", "unknown"),
            "file_size_bytes": 0,
            "total_pages": max((c["metadata"].get("page_number", 1) for c in chunks), default=1),
            "total_chunks": len(chunks),
            "category": first_chunk_meta.get("category", "placement"),
            "status": "ready",
            "uploaded_at": "",
        }

    item = DocumentItem(**doc_data)
    return DocumentDetailResponse(document=item, chunks_count=len(chunks))


@router.delete(
    "/{document_id}",
    response_model=DocumentDeleteResponse,
    summary="Delete a document and its vectors from ChromaDB",
)
def delete_document(
    document_id: str,
    current_user: Optional[UserProfile] = Depends(get_optional_current_user),
):
    """Validates document ownership before deleting from ChromaDB and MongoDB."""
    mongo = MongoDBManager.get_instance()
    vector_store = VectorStoreService()

    # Strict ownership permission check
    if mongo.is_connected:
        owner = mongo.get_document_owner(document_id)
        if owner and current_user and owner != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to delete this document. It belongs to another user.",
            )

    deleted_chunks = vector_store.delete_document(document_id)
    if mongo.is_connected:
        user_id = current_user.user_id if current_user else None
        mongo.delete_document(document_id, user_id=user_id)

    from backend.app.services.bm25 import BM25Service
    BM25Service.get_instance().refresh()

    if deleted_chunks == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{document_id}' does not exist or has already been deleted.",
        )

    return DocumentDeleteResponse(
        document_id=document_id,
        message=f"Document '{document_id}' and all associated {deleted_chunks} vectors deleted successfully.",
        deleted_chunks=deleted_chunks,
    )
