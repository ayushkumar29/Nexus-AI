"""Document processing service using PyMuPDF (fitz).

Responsibilities:
- Open and parse PDF files.
- Extract text page by page preserving 1-based page numbers.
- Normalize whitespace and strip common extraction artifacts.
- Detect encrypted PDFs, malformed documents, and PDFs with no extractable text.
"""

import logging
import re
from dataclasses import dataclass
from typing import List
import pymupdf

logger = logging.getLogger("nexus_ai.pdf_processing")


class DocumentProcessingError(Exception):
    """Exception raised when document parsing or extraction fails."""

    def __init__(self, message: str, is_malformed: bool = False, is_encrypted: bool = False, has_no_text: bool = False):
        super().__init__(message)
        self.message = message
        self.is_malformed = is_malformed
        self.is_encrypted = is_encrypted
        self.has_no_text = has_no_text


@dataclass
class PageText:
    """Extracted text and metadata for a single document page."""

    page_number: int  # 1-based index
    text: str


class PDFProcessorService:
    """Service for opening, verifying, and extracting text from PDF files."""

    @staticmethod
    def normalize_text(text: str) -> str:
        """Clean and normalize raw extracted PDF text.

        - Replaces control characters and form feeds.
        - Joins hyphenated words across soft line breaks (e.g. 'com-\nplete' -> 'complete').
        - Collapses repeated excessive blank lines and horizontal whitespace without destroying paragraphs.
        """
        if not text:
            return ""

        # Normalize carriage returns and form feeds
        normalized = text.replace("\r\n", "\n").replace("\r", "\n").replace("\f", "\n")

        # Reconnect hyphenated word breaks at line ends
        normalized = re.sub(r"(\w+)-\n(\w+)", r"\1\2", normalized)

        # Replace non-breaking spaces and tabs with standard space
        normalized = re.sub(r"[ \t\u00a0]+", " ", normalized)

        # Remove standalone non-printable control characters (except newline)
        normalized = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]", "", normalized)

        # Normalize excessive newlines (more than 2 consecutive becomes 2)
        normalized = re.sub(r"\n{3,}", "\n\n", normalized)

        # Strip whitespace on lines
        lines = [line.strip() for line in normalized.split("\n")]
        return "\n".join(lines).strip()

    def process_pdf(self, file_path: str) -> List[PageText]:
        """Open, validate, and extract clean text from a PDF file page by page.

        Raises DocumentProcessingError on failures (encrypted, malformed, empty, or no text).
        """
        try:
            doc = pymupdf.open(file_path)
        except Exception as exc:
            logger.error(f"Failed to open PDF at {file_path}: {exc}")
            raise DocumentProcessingError(
                message=f"Malformed or unreadable PDF document: {str(exc)}",
                is_malformed=True,
            ) from exc

        try:
            # Check for encryption
            if doc.is_encrypted:
                logger.warning(f"Encrypted PDF rejected: {file_path}")
                raise DocumentProcessingError(
                    message="Encrypted or password-protected PDF files are not supported.",
                    is_encrypted=True,
                )

            page_count = len(doc)
            if page_count == 0:
                logger.warning(f"Empty PDF rejected (0 pages): {file_path}")
                raise DocumentProcessingError(
                    message="PDF document contains zero pages.",
                    is_malformed=True,
                )

            pages: List[PageText] = []
            total_extracted_chars = 0

            for page_idx in range(page_count):
                page = doc[page_idx]
                raw_text = page.get_text("text") or ""
                cleaned = self.normalize_text(raw_text)

                total_extracted_chars += len(cleaned)
                # Keep page entry even if individual page is blank (e.g. image-only page in a document)
                pages.append(PageText(page_number=page_idx + 1, text=cleaned))

            if total_extracted_chars == 0:
                logger.warning(f"PDF contains no extractable text: {file_path}")
                raise DocumentProcessingError(
                    message="Document contains no extractable text. Scanned or image-only PDFs without OCR are not supported.",
                    has_no_text=True,
                )

            logger.info(f"Successfully processed PDF {file_path}: {page_count} pages, {total_extracted_chars} characters.")
            return pages

        finally:
            doc.close()
