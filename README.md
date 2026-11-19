# Nexus AI — Enterprise Knowledge Assistant

Nexus AI is an enterprise-grade AI knowledge assistant built with Python, FastAPI, PostgreSQL, SQLAlchemy 2.0, Alembic, PyMuPDF, React, and TypeScript.

---

## Architecture Overview

Nexus AI is engineered with a strict separation of concerns, decoupling presentation, orchestration, domain logic, data persistence, and schemas across independent backend and frontend services.

```
Nexus-AI/
├── backend/
│   ├── alembic/                 # Database migrations with Alembic
│   │   ├── versions/            # Migration revisions
│   │   │   ├── 79e44e4ca26b_create_users_table.py
│   │   │   └── e06af26617f5_create_documents_and_chunks_tables.py
│   │   └── env.py               # Alembic runner with application config
│   ├── app/
│   │   ├── api/
│   │   │   ├── deps.py          # Dependencies: OAuth2 bearer & current user
│   │   │   └── routes/          # API route definitions and sub-routers
│   │   │       ├── __init__.py  # Aggregated v1 router
│   │   │       ├── auth.py      # Registration, login, /me routes
│   │   │       ├── documents.py # Document upload, listing, chunks & deletion (M3.1)
│   │   │       └── health.py    # Health & telemetry endpoint (/api/v1/health)
│   │   ├── core/                # Configuration, logging, centralized exceptions, security
│   │   │   ├── config.py        # Pydantic Settings & environment variables
│   │   │   ├── exceptions.py    # Global exception handlers
│   │   │   └── security.py      # Argon2 password hashing & JWT handling
│   │   ├── db/                  # Database session and connection pooling
│   │   │   ├── __init__.py
│   │   │   └── session.py       # Engine with QueuePool, Base, and get_db dependency
│   │   ├── models/              # SQLAlchemy 2.0 ORM domain entities
│   │   │   ├── __init__.py
│   │   │   ├── user.py          # User ORM model
│   │   │   └── document.py      # Document and DocumentChunk ORM models
│   │   ├── schemas/             # Pydantic v2 schemas for request/response validation
│   │   │   ├── health.py        # HealthCheckResponse schema
│   │   │   ├── user.py          # User request and response schemas
│   │   │   └── document.py      # Document & DocumentChunk request and response schemas
│   │   ├── services/            # Business & orchestration logic
│   │   │   ├── auth_service.py  # User registration, authentication & queries
│   │   │   ├── chunking_service.py # Sentence/paragraph boundary chunker with overlap
│   │   │   ├── document_service.py # Ingestion pipeline, streaming, storage, persistence
│   │   │   ├── health_service.py# Health service & database probe implementation
│   │   │   └── pdf_processor.py # PyMuPDF (fitz) text extraction & normalization
│   │   └── main.py              # FastAPI application factory and CORS middleware
│   ├── tests/                   # Pytest unit and integration test suite
│   │   ├── conftest.py          # Isolated in-memory DB fixtures and FastAPI TestClient
│   │   ├── test_auth.py         # M2.1 Auth tests (registration, duplicate, login, JWT)
│   │   ├── test_documents.py    # M3.1 Ingestion, PyMuPDF extraction, chunking, security
│   │   └── test_health.py       # Health check, DB probe, and CORS tests
│   ├── storage/
│   │   └── documents/           # Configurable directory for uploaded PDF files
│   ├── .env                     # Local environment configuration
│   ├── .env.example             # Template environment variables
│   ├── alembic.ini              # Alembic migration configuration
│   ├── pytest.ini               # Test configuration
│   ├── requirements.txt         # Python dependencies
│   └── run.py                   # Standalone backend server runner
│
└── frontend/
    ├── src/
    │   ├── components/
    │   │   ├── common/          # Reusable UI components
    │   │   │   └── PlaceholderView.tsx
    │   │   ├── dashboard/       # Dashboard-specific views and metrics
    │   │   │   ├── DashboardOverview.tsx
    │   │   │   └── MetricCard.tsx
    │   │   └── layout/          # Layout scaffolding
    │   │       ├── Header.tsx   # Control center header & refresh triggers
    │   │       └── Sidebar.tsx  # Navigation sidebar with live node indicator
    │   ├── services/            # Client-side API integration
    │   │   └── api.ts           # Type-safe fetch client for backend
    │   ├── types/               # TypeScript interfaces and contracts
    │   │   └── index.ts
    │   ├── App.tsx              # Root application component
    │   ├── main.tsx             # React DOM entrypoint
    │   └── index.css            # Dark enterprise design system
    ├── .env                     # Vite environment configuration
    ├── .env.example             # Frontend env template
    ├── package.json             # NPM dependencies & scripts
    └── vite.config.ts           # Vite build configuration
```

---

## Configuration Settings

Configure environment settings in `.env`:

```env
# Database
POSTGRES_SERVER=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=nexus_ai

# Connection Pool Settings
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=1800

# Authentication
SECRET_KEY=your-secure-secret-key-min32chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Document Ingestion & Chunking (M3.1)
STORAGE_DIR="./storage/documents"
MAX_UPLOAD_SIZE_BYTES=20971520 # 20 MB
CHUNK_SIZE_TOKENS=700
CHUNK_OVERLAP_TOKENS=100
```

---

## Database Migrations

Run database migrations to initialize or update schema:

```bash
cd backend

# Apply migrations to head
.venv\Scripts\alembic upgrade head

# Generate a new migration revision
.venv\Scripts\alembic revision --autogenerate -m "describe changes"
```

---

## Backend Setup & Execution

### 1. Initialize Virtual Environment & Dependencies

From repository root:

```bash
cd backend
python -m venv .venv

# On Windows:
.venv\Scripts\pip install -r requirements.txt

# On macOS/Linux:
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Run the Backend Server

```bash
.venv\Scripts\python run.py
```
- API Base URL: `http://127.0.0.1:8000/api/v1`
- Interactive Swagger UI: `http://127.0.0.1:8000/docs`

### 3. Run Backend Tests

```bash
cd backend
.venv\Scripts\pytest -v
```

All 23 automated unit and integration tests execute against an isolated test database with table resets per test.

---

## Document Processing & Ingestion Pipeline

1. **Validation & Streaming**:
   `POST /api/v1/documents/upload` accepts `multipart/form-data`. The file is streamed in 64 KB chunks to verify magic bytes (`%PDF-`), ensure file size does not exceed `MAX_UPLOAD_SIZE_BYTES` (20 MB), and calculate the SHA-256 hash. Duplicate uploads for the same user are rejected with `409 Conflict`.
2. **Storage Isolation**:
   Files are stored in `STORAGE_DIR` using randomized UUID filenames (`<uuid>.pdf`), protecting against directory traversal and path exposure.
3. **Extraction**:
   `PDFProcessorService` uses PyMuPDF (`fitz`) to validate non-encryption, extract text page-by-page preserving 1-based page indices, reconnect hyphenated line wraps, and normalize whitespace. PDFs without extractable text or with encryption are flagged as `FAILED` with safe error explanations.
4. **Chunking**:
   `ChunkingService` segments text along sentence boundaries (`re.split`), sliding a window targeting ~700 tokens per chunk with ~100 tokens overlap, preserving page boundaries (`page_start`, `page_end`) and metadata (`character_count`, `sentence_count`).
5. **Transactional Persistence**:
   The `Document` and all associated `DocumentChunk` records are persisted in a single transaction. Deleting a document removes chunks via database cascade and unlinks the local file from disk.

---

## API Endpoints

| Method | Endpoint | Description | Auth Required | Status Codes |
|---|---|---|---|---|
| `GET` | `/api/v1/health` | System diagnostics & DB connectivity | No | 200 OK |
| `POST` | `/api/v1/auth/register` | Register new user | No | 201 Created, 409 Conflict, 422 Unprocessable |
| `POST` | `/api/v1/auth/login` | Authenticate user & issue JWT | No | 200 OK, 401 Unauthorized, 403 Forbidden |
| `GET` | `/api/v1/auth/me` | Fetch authenticated profile | Bearer JWT | 200 OK, 401 Unauthorized, 403 Forbidden |
| `POST` | `/api/v1/documents/upload` | Upload & ingest PDF file | Bearer JWT | 201 Created, 400 Bad Request, 409 Conflict, 413 Too Large |
| `GET` | `/api/v1/documents/` | List user documents (paginated) | Bearer JWT | 200 OK, 401 Unauthorized |
| `GET` | `/api/v1/documents/{document_id}` | Get document metadata | Bearer JWT | 200 OK, 401 Unauthorized, 404 Not Found |
| `GET` | `/api/v1/documents/{document_id}/chunks` | Get all document chunks | Bearer JWT | 200 OK, 401 Unauthorized, 404 Not Found |
| `DELETE` | `/api/v1/documents/{document_id}` | Delete document, chunks & file | Bearer JWT | 204 No Content, 401 Unauthorized, 404 Not Found |
