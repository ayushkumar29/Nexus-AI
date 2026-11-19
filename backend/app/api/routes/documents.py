"""Document ingestion and retrieval endpoints."""

from typing import Annotated
from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.models.user import User
from app.schemas.document import (
    DocumentChunkListResponse,
    DocumentChunkResponse,
    DocumentListResponse,
    DocumentResponse,
)
from app.services.document_service import DocumentService

router = APIRouter(prefix="/documents", tags=["Documents"])


def get_document_service(
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> DocumentService:
    """Dependency provider for DocumentService."""
    return DocumentService(db, settings=settings)


@router.post(
    "/upload",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and Process PDF Document",
    description="Uploads a PDF document (up to 20MB), verifies format, extracts text with PyMuPDF, and creates chunks.",
)
async def upload_document(
    file: Annotated[UploadFile, File(...)],
    current_user: Annotated[User, Depends(get_current_user)],
    document_service: Annotated[DocumentService, Depends(get_document_service)],
) -> DocumentResponse:
    """Upload a PDF, extract its content, and store structured chunks."""
    # 1. Stream, validate magic bytes, check duplicates, write to storage
    safe_name, file_path, file_size, file_hash = await document_service.save_and_verify_upload(
        file=file,
        user_id=current_user.id,
    )

    # 2. Extract, chunk, and persist
    document = document_service.process_and_persist_document(
        user_id=current_user.id,
        filename=safe_name,
        file_path=file_path,
        file_size=file_size,
        file_hash=file_hash,
    )

    return DocumentResponse.model_validate(document)


@router.get(
    "/",
    response_model=DocumentListResponse,
    status_code=status.HTTP_200_OK,
    summary="List User Documents",
    description="Lists documents belonging to the authenticated user with pagination.",
)
async def list_documents(
    current_user: Annotated[User, Depends(get_current_user)],
    document_service: Annotated[DocumentService, Depends(get_document_service)],
    skip: int = Query(0, ge=0, description="Number of documents to skip"),
    limit: int = Query(20, ge=1, le=100, description="Max documents to return"),
) -> DocumentListResponse:
    """List paginated documents for authenticated user."""
    items, total = document_service.get_user_documents(
        user_id=current_user.id,
        skip=skip,
        limit=limit,
    )
    return DocumentListResponse(
        items=[DocumentResponse.model_validate(item) for item in items],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Document by ID",
    description="Retrieves document metadata for an owned document.",
)
async def get_document(
    document_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    document_service: Annotated[DocumentService, Depends(get_document_service)],
) -> DocumentResponse:
    """Get metadata for specific document."""
    doc = document_service.get_document_by_id(document_id, current_user.id)
    return DocumentResponse.model_validate(doc)


@router.get(
    "/{document_id}/chunks",
    response_model=DocumentChunkListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Document Chunks",
    description="Retrieves all extracted chunks and metadata for an owned document.",
)
async def get_document_chunks(
    document_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    document_service: Annotated[DocumentService, Depends(get_document_service)],
) -> DocumentChunkListResponse:
    """Get text chunks for specific document."""
    chunks = document_service.get_document_chunks(document_id, current_user.id)
    return DocumentChunkListResponse(
        document_id=document_id,
        total_chunks=len(chunks),
        chunks=[DocumentChunkResponse.model_validate(c) for c in chunks],
    )


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Document",
    description="Deletes a document, its database chunks, and its stored physical file.",
)
async def delete_document(
    document_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    document_service: Annotated[DocumentService, Depends(get_document_service)],
) -> None:
    """Delete document and remove associated chunks."""
    document_service.delete_document(document_id, current_user.id)
    return None
