"""Pydantic schemas for documents and document chunks."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.models.document import ProcessingStatus


class DocumentBase(BaseModel):
    """Base schema for document metadata."""

    filename: str = Field(..., description="Original uploaded filename")
    file_size: int = Field(..., description="File size in bytes")
    file_hash: str = Field(..., description="SHA-256 hash of the file")
    page_count: int = Field(default=0, description="Number of pages extracted")
    processing_status: ProcessingStatus = Field(default=ProcessingStatus.PENDING)
    error_message: Optional[str] = Field(default=None, description="Error details if processing failed")


class DocumentResponse(DocumentBase):
    """Public document response returned to clients (internal path omitted)."""

    id: int = Field(..., description="Unique document identifier")
    user_id: int = Field(..., description="Owner user identifier")
    created_at: datetime = Field(..., description="Upload timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = ConfigDict(from_attributes=True)


class DocumentListResponse(BaseModel):
    """Paginated list of user documents."""

    items: List[DocumentResponse] = Field(..., description="List of documents")
    total: int = Field(..., description="Total documents matching query")
    skip: int = Field(..., description="Offset pagination index")
    limit: int = Field(..., description="Page limit")


class DocumentChunkResponse(BaseModel):
    """Document chunk response schema."""

    id: int = Field(..., description="Unique chunk identifier")
    document_id: int = Field(..., description="Parent document identifier")
    chunk_index: int = Field(..., description="Zero-based chunk position index")
    page_start: int = Field(..., description="First page number included in chunk (1-based)")
    page_end: int = Field(..., description="Last page number included in chunk (1-based)")
    content: str = Field(..., description="Text content of the chunk")
    token_count: int = Field(..., description="Approximate token count")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        validation_alias="metadata_",
        description="Chunk metadata and references",
    )

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class DocumentChunkListResponse(BaseModel):
    """List of chunks for a document."""

    document_id: int = Field(..., description="Parent document identifier")
    total_chunks: int = Field(..., description="Total chunks for document")
    chunks: List[DocumentChunkResponse] = Field(..., description="Ordered list of document chunks")
