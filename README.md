# Nexus AI — Enterprise Knowledge Assistant

Nexus AI is an enterprise-grade AI knowledge assistant built with Python, FastAPI, PostgreSQL, SQLAlchemy 2.0, Alembic, React, and TypeScript.

---

## Architecture Overview

Nexus AI is engineered with a strict separation of concerns, decoupling presentation, orchestration, domain logic, data persistence, and schemas across independent backend and frontend services.

```
Nexus-AI/
├── backend/
│   ├── alembic/                 # Database migrations with Alembic
│   │   ├── versions/            # Migration revisions
│   │   │   └── 79e44e4ca26b_create_users_table.py
│   │   └── env.py               # Alembic runner with application config
│   ├── app/
│   │   ├── api/
│   │   │   ├── deps.py          # Dependencies: OAuth2 bearer & current user
│   │   │   └── routes/          # API route definitions and sub-routers
│   │   │       ├── __init__.py  # Aggregated v1 router
│   │   │       ├── auth.py      # Registration, login, /me routes
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
│   │   │   └── user.py          # User ORM model
│   │   ├── schemas/             # Pydantic v2 schemas for request/response validation
│   │   │   ├── health.py        # HealthCheckResponse schema
│   │   │   └── user.py          # UserRegisterRequest, UserLoginRequest, UserResponse, TokenResponse
│   │   ├── services/            # Business & orchestration logic
│   │   │   ├── auth_service.py  # User registration, authentication & queries
│   │   │   └── health_service.py# Health service & database probe implementation
│   │   └── main.py              # FastAPI application factory and CORS middleware
│   ├── tests/                   # Pytest unit and integration test suite
│   │   ├── conftest.py          # Isolated in-memory DB fixtures and FastAPI TestClient
│   │   ├── test_auth.py         # M2.1 Auth tests (registration, duplicate, invalid, login, JWT)
│   │   └── test_health.py       # Health check, DB probe, and CORS tests
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

## Database Setup & Configuration

### PostgreSQL Configuration

Configure PostgreSQL connection settings in `.env`:

```env
POSTGRES_SERVER=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=nexus_ai

# Or pass a full connection URL:
# DATABASE_URL=postgresql+psycopg2://postgres:your_secure_password@localhost:5432/nexus_ai

# Connection Pool Settings
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=1800
```

> **Note**: For local development without a running PostgreSQL instance, `DATABASE_URL=sqlite:///./nexus_ai_dev.db` is supported out-of-the-box. Tests run automatically in an isolated in-memory SQLite database.

### Alembic Migrations

Run database migrations to initialize or update schema:

```bash
cd backend

# Apply migrations to head
.venv\Scripts\alembic upgrade head

# Generate a new migration revision (if models change)
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

All 12 automated unit and integration tests execute against an isolated test database with rolled-back transactions per test.

---

## Authentication Flow

1. **User Registration**:
   `POST /api/v1/auth/register` validates email syntax and password length (min 8 chars), verifies email uniqueness, and securely hashes passwords using **Argon2id**. Plaintext passwords are never persisted.
2. **User Login**:
   `POST /api/v1/auth/login` checks credentials via Argon2 verification and issues a signed **JWT Bearer Token** expiring according to `ACCESS_TOKEN_EXPIRE_MINUTES`.
3. **Protected Endpoint**:
   `GET /api/v1/auth/me` expects `Authorization: Bearer <token>`. The `get_current_user` dependency decodes the token, checks signature and expiration, and retrieves the active user from the database.

---

## API Endpoints

| Method | Endpoint | Description | Auth Required | Status Codes |
|---|---|---|---|---|
| `GET` | `/api/v1/health` | System diagnostics & DB connectivity | No | 200 OK |
| `POST` | `/api/v1/auth/register` | Register new user | No | 201 Created, 409 Conflict, 422 Unprocessable |
| `POST` | `/api/v1/auth/login` | Authenticate user & issue JWT | No | 200 OK, 401 Unauthorized, 403 Forbidden |
| `GET` | `/api/v1/auth/me` | Fetch authenticated profile | Bearer JWT | 200 OK, 401 Unauthorized, 403 Forbidden |
