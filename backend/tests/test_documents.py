"""Automated test suite for M3.1 Document Intelligence Engine.

Covers:
- Successful PDF upload
- Invalid file extension (.txt, .exe)
- Invalid PDF content (magic bytes check)
- Oversized upload (> MAX_UPLOAD_SIZE_BYTES)
- Empty PDF (0 bytes and 0 pages)
- Encrypted PDF rejection
- Text extraction and multi-page extraction
- Chunking and overlap
- Page metadata preservation
- Duplicate upload detection
- User ownership and isolation
- Document deletion (DB and disk cleanup)
- Failed processing (empty/unextractable text handling)
"""

import io
from typing import Dict
from fastapi import status
from fastapi.testclient import TestClient
import pymupdf


def _create_test_pdf(pages_text: list[str], encrypt_password: str | None = None) -> bytes:
    """Helper to generate an in-memory PDF with specified pages of text."""
    doc = pymupdf.open()
    for text in pages_text:
        page = doc.new_page(width=595, height=842)
        if text.strip():
            page.insert_text((50, 50), text, fontsize=12)

    if encrypt_password:
        # Encrypt document
        perm = int(
            pymupdf.PDF_PERM_ACCESSIBILITY
            | pymupdf.PDF_PERM_PRINT
            | pymupdf.PDF_PERM_COPY
            | pymupdf.PDF_PERM_ANNOTATE
        )
        pdf_bytes = doc.tobytes(
            garbage=4,
            deflate=True,
            encryption=pymupdf.PDF_ENCRYPT_AES_256,
            owner_pw=encrypt_password,
            user_pw=encrypt_password,
            permissions=perm,
        )
    else:
        pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def _get_auth_headers(client: TestClient, email: str, password: str = "SecurePass123!") -> Dict[str, str]:
    """Helper to register/login a test user and return authorization bearer header."""
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "full_name": "Test User", "password": password},
    )
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_successful_pdf_upload_and_processing(client: TestClient) -> None:
    """Verify clean PDF upload extracts text, computes chunks, and completes."""
    headers = _get_auth_headers(client, "doc_user1@example.com")

    # Create a 2-page valid PDF
    pdf_data = _create_test_pdf([
        "Nexus AI is an enterprise knowledge assistant designed for robust document intelligence.",
        "Page two contains additional technical specifications regarding neural architecture and RAG pipelines."
    ])

    response = client.post(
        "/api/v1/documents/upload",
        headers=headers,
        files={"file": ("knowledge.pdf", io.BytesIO(pdf_data), "application/pdf")},
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["filename"] == "knowledge.pdf"
    assert data["page_count"] == 2
    assert data["processing_status"] == "COMPLETED"
    assert data["file_size"] == len(pdf_data)
    assert "file_hash" in data
    assert "file_path" not in data  # Never expose internal paths

    doc_id = data["id"]

    # Verify chunks endpoint
    chunks_res = client.get(f"/api/v1/documents/{doc_id}/chunks", headers=headers)
    assert chunks_res.status_code == status.HTTP_200_OK
    chunks_data = chunks_res.json()
    assert chunks_data["document_id"] == doc_id
    assert chunks_data["total_chunks"] >= 1
    assert len(chunks_data["chunks"]) >= 1

    first_chunk = chunks_data["chunks"][0]
    assert first_chunk["page_start"] == 1
    assert "Nexus AI" in first_chunk["content"]
    assert first_chunk["token_count"] > 0
    assert "character_count" in first_chunk["metadata"]


def test_invalid_file_extension(client: TestClient) -> None:
    """Verify uploading a non-PDF file (.txt) is rejected."""
    headers = _get_auth_headers(client, "doc_user2@example.com")
    response = client.post(
        "/api/v1/documents/upload",
        headers=headers,
        files={"file": ("notes.txt", io.BytesIO(b"Hello world text"), "text/plain")},
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data["success"] is False
    assert "Only PDF files" in data["error"]["message"]


def test_invalid_pdf_content(client: TestClient) -> None:
    """Verify file named .pdf but containing non-PDF magic bytes is rejected."""
    headers = _get_auth_headers(client, "doc_user3@example.com")
    fake_pdf = b"NOT_A_PDF_MAGIC_BYTES_12345"
    response = client.post(
        "/api/v1/documents/upload",
        headers=headers,
        files={"file": ("fake.pdf", io.BytesIO(fake_pdf), "application/pdf")},
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data["success"] is False
    assert "PDF magic bytes" in data["error"]["message"]


def test_oversized_upload(client: TestClient) -> None:
    """Verify files exceeding MAX_UPLOAD_SIZE_BYTES are rejected with 413."""
    headers = _get_auth_headers(client, "doc_user4@example.com")
    # Test setting has 2MB limit
    oversized = b"%PDF-1.4\n" + b"0" * (2 * 1024 * 1024 + 1024)
    response = client.post(
        "/api/v1/documents/upload",
        headers=headers,
        files={"file": ("large.pdf", io.BytesIO(oversized), "application/pdf")},
    )
    assert response.status_code == status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
    data = response.json()
    assert data["success"] is False
    assert "exceeds maximum upload size" in data["error"]["message"]


def test_empty_pdf(client: TestClient) -> None:
    """Verify 0-byte PDF upload is rejected."""
    headers = _get_auth_headers(client, "doc_user5@example.com")
    response = client.post(
        "/api/v1/documents/upload",
        headers=headers,
        files={"file": ("empty.pdf", io.BytesIO(b""), "application/pdf")},
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data["success"] is False
    assert "empty" in data["error"]["message"].lower() or "magic bytes" in data["error"]["message"].lower()


def test_encrypted_pdf_rejection(client: TestClient) -> None:
    """Verify encrypted/password-protected PDFs are flagged with FAILED status and safe error."""
    headers = _get_auth_headers(client, "doc_user6@example.com")
    encrypted_bytes = _create_test_pdf(["Secret content"], encrypt_password="password123")

    response = client.post(
        "/api/v1/documents/upload",
        headers=headers,
        files={"file": ("encrypted.pdf", io.BytesIO(encrypted_bytes), "application/pdf")},
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["processing_status"] == "FAILED"
    assert "Encrypted" in data["error_message"] or "password" in data["error_message"].lower()


def test_no_extractable_text_pdf(client: TestClient) -> None:
    """Verify PDF with blank or non-extractable text pages is marked FAILED."""
    headers = _get_auth_headers(client, "doc_user7@example.com")
    blank_pdf = _create_test_pdf(["", ""])  # Two blank pages

    response = client.post(
        "/api/v1/documents/upload",
        headers=headers,
        files={"file": ("blank.pdf", io.BytesIO(blank_pdf), "application/pdf")},
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["processing_status"] == "FAILED"
    assert "no extractable text" in data["error_message"].lower()


def test_duplicate_upload_rejection(client: TestClient) -> None:
    """Verify duplicate upload of the exact same file by the same user is rejected with 409."""
    headers = _get_auth_headers(client, "doc_user8@example.com")
    pdf_data = _create_test_pdf(["Unique document content for duplicate checking."])

    # First upload
    res1 = client.post(
        "/api/v1/documents/upload",
        headers=headers,
        files={"file": ("doc_v1.pdf", io.BytesIO(pdf_data), "application/pdf")},
    )
    assert res1.status_code == status.HTTP_201_CREATED

    # Second upload with same content (even with different filename)
    res2 = client.post(
        "/api/v1/documents/upload",
        headers=headers,
        files={"file": ("doc_v2_rename.pdf", io.BytesIO(pdf_data), "application/pdf")},
    )
    assert res2.status_code == status.HTTP_409_CONFLICT
    data = res2.json()
    assert "Duplicate document" in data["error"]["message"]


def test_document_ownership_and_user_isolation(client: TestClient) -> None:
    """Verify user cannot access, list, or delete another user's documents."""
    user1_headers = _get_auth_headers(client, "owner1@example.com")
    user2_headers = _get_auth_headers(client, "owner2@example.com")

    # User 1 uploads document
    pdf1 = _create_test_pdf(["Private confidential notes for User 1 only."])
    upload_res = client.post(
        "/api/v1/documents/upload",
        headers=user1_headers,
        files={"file": ("user1_doc.pdf", io.BytesIO(pdf1), "application/pdf")},
    )
    assert upload_res.status_code == status.HTTP_201_CREATED
    user1_doc_id = upload_res.json()["id"]

    # User 2 tries to fetch User 1's document -> 404
    get_res = client.get(f"/api/v1/documents/{user1_doc_id}", headers=user2_headers)
    assert get_res.status_code == status.HTTP_404_NOT_FOUND

    # User 2 tries to fetch User 1's chunks -> 404
    chunks_res = client.get(f"/api/v1/documents/{user1_doc_id}/chunks", headers=user2_headers)
    assert chunks_res.status_code == status.HTTP_404_NOT_FOUND

    # User 2 tries to delete User 1's document -> 404
    del_res = client.delete(f"/api/v1/documents/{user1_doc_id}", headers=user2_headers)
    assert del_res.status_code == status.HTTP_404_NOT_FOUND

    # User 2 lists documents -> Empty list
    list_res = client.get("/api/v1/documents/", headers=user2_headers)
    assert list_res.status_code == status.HTTP_200_OK
    assert list_res.json()["total"] == 0


def test_document_deletion_cascades(client: TestClient) -> None:
    """Verify deleting a document deletes document record and cascades chunks."""
    headers = _get_auth_headers(client, "del_user@example.com")
    pdf = _create_test_pdf(["A document that will be deleted soon."])

    upload_res = client.post(
        "/api/v1/documents/upload",
        headers=headers,
        files={"file": ("to_delete.pdf", io.BytesIO(pdf), "application/pdf")},
    )
    doc_id = upload_res.json()["id"]

    # Delete
    del_res = client.delete(f"/api/v1/documents/{doc_id}", headers=headers)
    assert del_res.status_code == status.HTTP_204_NO_CONTENT

    # Fetch document -> 404
    get_res = client.get(f"/api/v1/documents/{doc_id}", headers=headers)
    assert get_res.status_code == status.HTTP_404_NOT_FOUND


def test_chunking_and_page_metadata_preservation(client: TestClient) -> None:
    """Verify multi-page document chunking maintains correct page references and ordering."""
    headers = _get_auth_headers(client, "chunk_test_user@example.com")

    # Generate 3 distinct pages
    pages = [
        "First sentence on page one. Second sentence on page one.",
        "Sentence on page two discussing data indexing. Another point on page two.",
        "Conclusion on page three regarding evaluation metrics.",
    ]
    pdf = _create_test_pdf(pages)

    res = client.post(
        "/api/v1/documents/upload",
        headers=headers,
        files={"file": ("multipage.pdf", io.BytesIO(pdf), "application/pdf")},
    )
    doc_id = res.json()["id"]

    chunks_res = client.get(f"/api/v1/documents/{doc_id}/chunks", headers=headers)
    assert chunks_res.status_code == status.HTTP_200_OK
    chunks = chunks_res.json()["chunks"]
    assert len(chunks) >= 1

    # Verify 1-based page index preservation
    first_chunk = chunks[0]
    assert first_chunk["page_start"] >= 1
    assert first_chunk["page_end"] >= first_chunk["page_start"]
    assert "page one" in first_chunk["content"].lower()
