"""Document service orchestrating upload, validation, persistence, and chunking."""

import hashlib
import logging
import os
import uuid
from pathlib import Path
from typing import List, Optional, Tuple
from fastapi import UploadFile
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.exceptions import AppException
from app.models.document import Document, DocumentChunk, ProcessingStatus
from app.services.chunking_service import ChunkingService
from app.services.pdf_processor import DocumentProcessingError, PDFProcessorService

logger = logging.getLogger("nexus_ai.documents")


class DocumentService:
    """Service layer managing document upload, extraction pipeline, and queries."""

    def __init__(self, db: Session, settings: Optional[Settings] = None) -> None:
        self.db = db
        self.settings = settings or get_settings()
        self.pdf_processor = PDFProcessorService()
        self.chunker = ChunkingService(
            target_chunk_tokens=self.settings.CHUNK_SIZE_TOKENS,
            overlap_tokens=self.settings.CHUNK_OVERLAP_TOKENS,
        )

        # Ensure storage directory exists
        self.storage_path = Path(self.settings.STORAGE_DIR).resolve()
        self.storage_path.mkdir(parents=True, exist_ok=True)

    def _sanitize_filename(self, filename: Optional[str]) -> str:
        """Strip dangerous path characters to prevent directory traversal."""
        if not filename:
            return "document.pdf"
        base = os.path.basename(filename.strip())
        clean = "".join(c for c in base if c.isalnum() or c in (".", "-", "_")).strip()
        return clean or "document.pdf"

    async def save_and_verify_upload(
        self,
        file: UploadFile,
        user_id: int,
    ) -> Tuple[str, str, int, str]:
        """Stream upload file in chunks, calculate SHA-256 hash, enforce size limits,

        verify PDF magic bytes, and save with UUID filename.
        Returns (safe_filename, target_file_path, file_size, sha256_hash).
        """
        # 1. Validate file extension
        raw_name = file.filename or ""
        if not raw_name.lower().endswith(".pdf"):
            raise AppException(
                message="Invalid file type. Only PDF files (.pdf) are accepted.",
                status_code=400,
            )

        safe_name = self._sanitize_filename(raw_name)

        # 2. Generate secure UUID filename to prevent collisions and path traversal
        file_uuid = uuid.uuid4().hex
        target_path = self.storage_path / f"{file_uuid}.pdf"

        hasher = hashlib.sha256()
        total_size = 0
        chunk_size = 64 * 1024  # 64 KB streaming chunks
        first_chunk = True

        try:
            with open(target_path, "wb") as out_file:
                while True:
                    chunk = await file.read(chunk_size)
                    if not chunk:
                        break

                    # Check PDF magic bytes on first chunk (%PDF-)
                    if first_chunk:
                        if not chunk.startswith(b"%PDF-"):
                            raise AppException(
                                message="Invalid file format. File does not start with valid PDF magic bytes.",
                                status_code=400,
                            )
                        first_chunk = False

                    total_size += len(chunk)
                    if total_size > self.settings.MAX_UPLOAD_SIZE_BYTES:
                        raise AppException(
                            message=f"File exceeds maximum upload size of {self.settings.MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)} MB.",
                            status_code=413,
                        )

                    hasher.update(chunk)
                    out_file.write(chunk)

            if total_size == 0:
                raise AppException(
                    message="Uploaded PDF file is empty.",
                    status_code=400,
                )

        except Exception as exc:
            # Clean up on failure
            if target_path.exists():
                try:
                    target_path.unlink()
                except OSError:
                    pass
            if isinstance(exc, AppException):
                raise exc
            logger.error(f"Error reading upload stream: {exc}")
            raise AppException(message=f"Failed to process upload stream: {str(exc)}", status_code=500) from exc

        file_hash = hasher.hexdigest()

        # Check duplicate upload for this user
        existing = (
            self.db.execute(
                select(Document).where(
                    Document.user_id == user_id,
                    Document.file_hash == file_hash,
                )
            )
            .scalars()
            .first()
        )
        if existing:
            # Clean up the newly uploaded duplicate file on disk
            if target_path.exists():
                try:
                    target_path.unlink()
                except OSError:
                    pass
            raise AppException(
                message=f"Duplicate document detected. This file has already been uploaded as document id {existing.id}.",
                status_code=409,
            )

        return safe_name, str(target_path), total_size, file_hash

    def process_and_persist_document(
        self,
        user_id: int,
        filename: str,
        file_path: str,
        file_size: int,
        file_hash: str,
    ) -> Document:
        """Create document in DB, extract text pages via PyMuPDF, chunk content,

        and persist chunks transactionally. If extraction fails, record FAILED status safely.
        """
        # 1. Create document in PENDING state
        doc = Document(
            user_id=user_id,
            filename=filename,
            file_path=file_path,
            file_size=file_size,
            file_hash=file_hash,
            processing_status=ProcessingStatus.PROCESSING,
        )
        self.db.add(doc)
        self.db.commit()
        self.db.refresh(doc)

        # 2. Extract text page by page
        try:
            pages = self.pdf_processor.process_pdf(file_path)
            doc.page_count = len(pages)

            # 3. Chunk extracted content
            chunks = self.chunker.chunk_pages(pages)

            # 4. Create DocumentChunk records
            for chunk_data in chunks:
                chunk_record = DocumentChunk(
                    document_id=doc.id,
                    chunk_index=chunk_data.chunk_index,
                    page_start=chunk_data.page_start,
                    page_end=chunk_data.page_end,
                    content=chunk_data.content,
                    token_count=chunk_data.token_count,
                    metadata_=chunk_data.metadata,
                )
                self.db.add(chunk_record)

            doc.processing_status = ProcessingStatus.COMPLETED
            doc.error_message = None
            self.db.commit()
            self.db.refresh(doc)
            logger.info(f"Document id={doc.id} successfully processed with {len(chunks)} chunks.")
            return doc

        except DocumentProcessingError as exc:
            logger.warning(f"Document id={doc.id} processing failed: {exc.message}")
            self.db.rollback()
            # Update status to FAILED safely
            doc_fail = self.db.get(Document, doc.id)
            if doc_fail:
                doc_fail.processing_status = ProcessingStatus.FAILED
                doc_fail.error_message = exc.message
                self.db.commit()
                self.db.refresh(doc_fail)
                return doc_fail
            raise

        except Exception as exc:
            logger.exception(f"Unexpected error processing document id={doc.id}: {exc}")
            self.db.rollback()
            doc_fail = self.db.get(Document, doc.id)
            if doc_fail:
                doc_fail.processing_status = ProcessingStatus.FAILED
                doc_fail.error_message = "An unexpected error occurred while parsing the document."
                self.db.commit()
                self.db.refresh(doc_fail)
                return doc_fail
            raise

    def get_user_documents(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[List[Document], int]:
        """List documents belonging to the authenticated user with pagination."""
        total_stmt = select(func.count(Document.id)).where(Document.user_id == user_id)
        total = self.db.scalar(total_stmt) or 0

        items_stmt = (
            select(Document)
            .where(Document.user_id == user_id)
            .order_by(Document.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        items = list(self.db.scalars(items_stmt).all())
        return items, total

    def get_document_by_id(self, document_id: int, user_id: int) -> Document:
        """Fetch document guaranteeing ownership isolation."""
        doc = (
            self.db.execute(
                select(Document).where(
                    Document.id == document_id,
                    Document.user_id == user_id,
                )
            )
            .scalars()
            .first()
        )
        if not doc:
            raise AppException(message="Document not found.", status_code=404)
        return doc

    def get_document_chunks(self, document_id: int, user_id: int) -> List[DocumentChunk]:
        """Fetch all chunks for a document belonging to the user."""
        # Ensure document exists and belongs to user
        self.get_document_by_id(document_id, user_id)

        chunks_stmt = (
            select(DocumentChunk)
            .where(DocumentChunk.document_id == document_id)
            .order_by(DocumentChunk.chunk_index.asc())
        )
        return list(self.db.scalars(chunks_stmt).all())

    def delete_document(self, document_id: int, user_id: int) -> None:
        """Delete document and all chunks, and remove file from disk."""
        doc = self.get_document_by_id(document_id, user_id)

        # Remove file from disk
        file_path = Path(doc.file_path)
        if file_path.exists():
            try:
                file_path.unlink()
            except OSError as exc:
                logger.warning(f"Could not delete physical file {file_path}: {exc}")

        # Delete database record (cascades to chunks)
        self.db.delete(doc)
        self.db.commit()
        logger.info(f"Deleted document id={document_id} and its associated chunks.")
