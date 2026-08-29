# Backend Structure Document
## GiftGenius - Exact File Organization & Code Architecture

**Purpose:** This document defines the precise file structure and code organization patterns that MUST be followed to maintain consistency and scalability.

**IMPORTANT:** Backend and Frontend are in **SEPARATE REPOSITORIES**. This document covers ONLY the backend repository structure.

---

## Backend Repository Root Structure

```
giftgenius-backend/              # Root of backend repository
├── .env                         # Environment variables (git-ignored)
├── .env.example                 # Template for .env (committed)
├── .gitignore                   # Git ignore rules
├── docker-compose.yml           # Multi-container orchestration
├── Dockerfile                   # Backend container definition
├── requirements.txt             # Python dependencies
├── .dockerignore               # Files to exclude from Docker build
├── README.md                    # Project documentation
│
└── app/                         # Main application package
    ├── __init__.py
    ├── main.py                  # FastAPI app entry point
    ├── database.py              # Database connection & session
    ├── models.py                # SQLModel table definitions
    ├── schemas.py               # Pydantic request/response models
    │
    ├── core/                    # Core utilities
    │   ├── __init__.py
    │   ├── config.py            # Settings from .env
    │   └── security.py          # JWT & password hashing
    │
    └── api/                     # API endpoints
        ├── __init__.py
        └── v1/                  # Version 1 of API
            ├── __init__.py
            ├── auth.py          # /register, /login
            ├── contacts.py      # CRUD for contacts
            └── memories.py      # CRUD for memories
```

**Note:** Frontend repository is separate and already built. Backend only needs to provide REST API endpoints that the frontend will consume.

---

## File-by-File Breakdown

### 1. `.env` (Git-Ignored)

**Location:** Repository root  
**Purpose:** Store secrets and environment-specific configuration

**Required Variables:**
```bash
# Database Configuration - Supabase
# Get this from: Supabase Dashboard → Settings → Database → Connection String (Session Mode)
DATABASE_URL=postgresql://postgres.[PROJECT-REF]:[YOUR-PASSWORD]@[REGION].pooler.supabase.com:5432/postgres

# JWT Configuration
SECRET_KEY=your-super-secret-key-min-32-characters-long-change-this
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Application
ENVIRONMENT=development
DEBUG=True
```

**Security Rules:**
- ✅ Never commit this file to git
- ✅ Use strong SECRET_KEY (generate with `openssl rand -hex 32`)
- ✅ Different values for dev/staging/production
- ✅ Get DATABASE_URL from Supabase project dashboard

---

### 2. `.env.example` (Committed to Git)

**Location:** Repository root  
**Purpose:** Template for other developers

**Content Structure:**
```bash
# Copy this file to .env and fill in actual values
# Get your Supabase connection string from: Dashboard → Settings → Database
DATABASE_URL=postgresql://postgres.[PROJECT-REF]:[PASSWORD]@[REGION].pooler.supabase.com:5432/postgres
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
ENVIRONMENT=development
DEBUG=True
```

---

### 3. `docker-compose.yml`

**Location:** Repository root  
**Purpose:** Define backend container (database is hosted by Supabase)

**Service Defined:**
- **backend service:** FastAPI application container

**Key Configuration Points:**
- Backend connects to Supabase managed PostgreSQL
- Port 8000 exposed for API
- Hot reload enabled with `--reload` flag
- Environment variables loaded from `.env` file

**Example Configuration:**
```yaml
version: '3.8'

services:
  backend:
    build: .
    container_name: giftgenius-backend
    ports:
      - "8000:8000"
    env_file:
      - .env
    volumes:
      - ./app:/app/app
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

### 4. `Dockerfile`

**Location:** Repository root  
**Purpose:** Define backend container image

**Build Steps:**
1. Use `python:3.10-slim` base image
2. Install system dependencies (gcc, postgresql-client)
3. Copy and install Python requirements
4. Copy application code
5. Expose port 8000
6. Run uvicorn server

---

### 5. `requirements.txt`

**Location:** Repository root  
**Purpose:** Pin Python dependencies with exact versions

**Categories of Dependencies:**

**Web Framework:**
- fastapi
- uvicorn[standard]

**Database:**
- sqlmodel
- psycopg2-binary
- alembic (optional for Phase 2)

**Authentication:**
- python-jose[cryptography]
- passlib[bcrypt]
- python-multipart

**Configuration:**
- python-dotenv
- pydantic-settings

**Utilities:**
- email-validator

---

### 6. `app/__init__.py`

**Location:** `app/__init__.py`  
**Purpose:** Make `app` a Python package

**Content:** Module docstring and version number

---

### 7. `app/main.py` (THE ENTRY POINT)

**Location:** `app/main.py`  
**Purpose:** FastAPI application initialization and configuration

**Responsibilities:**
- Create FastAPI app instance
- Configure CORS middleware (allow frontend origin `http://localhost:8080`)
- Include all API routers with `/api/v1` prefix
- Define lifespan events (startup: create DB tables, shutdown: cleanup)
- Provide health check endpoints

**Router Inclusions:**
- `/api/v1/auth` → auth.router (tag: "Authentication")
- `/api/v1/contacts` → contacts.router (tag: "Contacts")  
- `/api/v1/contacts` → memories.router (tag: "Memories")

**Important Endpoints:**
- `GET /` → API health check
- `GET /health` → Service health status

---

### 8. `app/database.py`

**Location:** `app/database.py`  
**Purpose:** Database connection and session management

**Key Components:**

**1. Engine Creation:**
- Loads DATABASE_URL from settings (Supabase connection string)
- Configures connection pool (size: 5, max_overflow: 10)
- Enables pool_pre_ping to prevent stale connections
- SQL query logging based on DEBUG flag

**Supabase Connection Notes:**
- Works seamlessly with Supabase PostgreSQL (no code changes needed)
- Use **Session Mode** pooler for persistent connections: `postgresql://postgres.[PROJECT-REF]:[PASSWORD]@[REGION].pooler.supabase.com:5432/postgres`
- Connection pooling is handled by both SQLAlchemy (client-side) and Supabase Supavisor (server-side)
- SSL is enabled by default for Supabase connections

**2. create_db_and_tables() Function:**
- Creates all database tables using SQLModel metadata
- Called during application startup
- Tables are created in your Supabase PostgreSQL database

**3. get_session() Dependency:**
- Yields database session for dependency injection
- Automatically handles commit/rollback
- Ensures session is closed after use

**Usage Pattern:**
```
def endpoint(session: Session = Depends(get_session)):
    # Use session here
```

---

### 9. `app/models.py` (DATABASE TABLES)

**Location:** `app/models.py`  
**Purpose:** SQLModel table definitions - source of truth for database schema

**Models Defined:**

**1. RelationshipType Enum:**
- Values: Friend, Family, Colleague, Partner, Other

**2. User Table:**
- Fields: id (UUID), email (unique, indexed), password_hash, created_at
- Relationship: One-to-many with Contact (cascade delete)

**3. Contact Table:**
- Fields: id (UUID), name, relationship_type (enum), birthday (optional), created_at
- Foreign Key: user_id → users.id (cascade delete)
- Relationships: Many-to-one with User, One-to-many with Memory

**4. Memory Table:**
- Fields: id (UUID), content (max 5000 chars), created_at
- Foreign Key: contact_id → contacts.id (cascade delete)
- Relationship: Many-to-one with Contact

**Key Design Decisions:**
- UUIDs for all primary keys (distributed system friendly)
- cascade_delete=True ensures no orphaned records
- created_at always uses UTC timezone
- Enums prevent invalid relationship types
- Max length constraints on text fields

---

### 10. `app/schemas.py` (API MODELS)

**Location:** `app/schemas.py`  
**Purpose:** Pydantic models for API request/response validation (separate from DB models)

**Schema Categories:**

**AUTH SCHEMAS:**
- UserRegister: email, password (min 8 chars)
- UserLogin: email, password
- Token: access_token, token_type
- UserResponse: id, email
- AuthResponse: access_token, token_type, user

**CONTACT SCHEMAS:**
- ContactCreate: name, relationship_type, birthday (optional)
- ContactResponse: id, name, relationship_type, birthday, created_at, memory_count (optional)
- ContactListResponse: contacts array

**MEMORY SCHEMAS:**
- MemoryCreate: content (1-5000 chars)
- MemoryResponse: id, content, created_at
- MemoryListResponse: memories array

**STANDARD RESPONSE ENVELOPES:**
- SuccessResponse: status="success", data, message (optional)
- ErrorResponse: status="error", data=null, message

**Config Notes:**
- Response models use `from_attributes = True` to work with ORM models

---

### 11. `app/core/config.py`

**Location:** `app/core/config.py`  
**Purpose:** Load and validate environment variables using Pydantic Settings

**Settings Class Fields:**

**Database:**
- DATABASE_URL (required)

**JWT:**
- SECRET_KEY (required)
- ALGORITHM (default: "HS256")
- ACCESS_TOKEN_EXPIRE_MINUTES (default: 1440 = 24 hours)

**Application:**
- ENVIRONMENT (default: "development")
- DEBUG (default: True)

**Configuration:**
- Reads from .env file
- Case sensitive variable names
- Creates global `settings` instance for import

---

### 12. `app/core/security.py`

**Location:** `app/core/security.py`  
**Purpose:** Authentication utilities - JWT and password hashing

**Components:**

**1. Password Hashing:**
- pwd_context: Bcrypt with 12 rounds
- hash_password(password) → hashed string
- verify_password(plain, hashed) → boolean

**2. JWT Token Management:**
- create_access_token(user_id) → JWT string
  - Payload: sub (user_id), exp (expiry), iat (issued at)
  - Signs with SECRET_KEY and ALGORITHM from settings
  
- decode_token(token) → user_id UUID
  - Validates signature and expiration
  - Raises HTTPException 401 if invalid

**3. FastAPI Dependency:**
- get_current_user_id(credentials) → user_id UUID
  - Extracts token from Authorization header
  - Validates and returns user ID
  - Use with `Depends(get_current_user_id)` in protected endpoints

**Security Features:**
- HTTPBearer scheme for token extraction
- Automatic 401 responses for invalid/expired tokens
- UTC timestamps for consistency

---

### 13. `app/api/__init__.py`

**Location:** `app/api/__init__.py`  
**Purpose:** Make `api` a Python package

**Content:** Empty or minimal docstring

---

### 14. `app/api/v1/__init__.py`

**Location:** `app/api/v1/__init__.py`  
**Purpose:** Make `v1` a Python package

**Content:** Empty or minimal docstring

---

### 15. `app/api/v1/auth.py`

**Location:** `app/api/v1/auth.py`  
**Purpose:** Authentication endpoints

**Endpoints Defined:**

**POST /register:**
- Input: UserRegister (email, password)
- Process: Check email uniqueness → Hash password → Create user → Generate JWT
- Output: SuccessResponse with access_token and user data
- Status: 201 Created
- Errors: 400 if email exists

**POST /login:**
- Input: UserLogin (email, password)
- Process: Find user → Verify password → Generate JWT
- Output: SuccessResponse with access_token and user data
- Status: 200 OK
- Errors: 401 if credentials invalid

**Both endpoints return the standard response envelope format.**

---

### 16. `app/api/v1/contacts.py`

**Location:** `app/api/v1/contacts.py`  
**Purpose:** Contact CRUD endpoints

**Endpoints Defined:**

**POST /contacts:**
- Protected: Requires JWT (Depends on get_current_user_id)
- Input: ContactCreate (name, relationship_type, birthday)
- Process: Create contact linked to authenticated user
- Output: SuccessResponse with contact data
- Status: 201 Created

**GET /contacts:**
- Protected: Requires JWT
- Process: Fetch all contacts for authenticated user, include memory count per contact
- Output: SuccessResponse with contacts array
- Status: 200 OK

**GET /contacts/{contact_id}:**
- Protected: Requires JWT
- Process: Fetch specific contact, verify ownership
- Output: SuccessResponse with contact data
- Status: 200 OK
- Errors: 404 if not found, 403 if not owned by user

**DELETE /contacts/{contact_id}:**
- Protected: Requires JWT
- Process: Delete contact and cascade delete all memories, verify ownership
- Output: SuccessResponse with null data
- Status: 200 OK
- Errors: 404 if not found, 403 if not owned by user

**Authorization Logic:**
- All endpoints verify user_id from JWT matches contact.user_id
- Prevents users from accessing other users' data

---

### 17. `app/api/v1/memories.py`

**Location:** `app/api/v1/memories.py`  
**Purpose:** Memory CRUD endpoints

**Endpoints Defined:**

**POST /contacts/{contact_id}/memories:**
- Protected: Requires JWT
- Input: MemoryCreate (content)
- Process: Verify contact exists and belongs to user → Create memory
- Output: SuccessResponse with memory data
- Status: 201 Created
- Errors: 404 if contact not found, 403 if contact not owned by user

**GET /contacts/{contact_id}/memories:**
- Protected: Requires JWT
- Process: Verify contact ownership → Fetch all memories sorted by created_at DESC (newest first)
- Output: SuccessResponse with memories array
- Status: 200 OK
- Errors: 404 if contact not found, 403 if contact not owned by user

**Authorization Logic:**
- Both endpoints verify contact.user_id matches authenticated user_id
- Ensures data isolation between users

---

## File Naming Conventions

**Python Files:**
- Use `snake_case.py` for all filenames
- Classes use `PascalCase`
- Functions use `snake_case`
- Constants use `UPPER_SNAKE_CASE`

**Examples:**
```
File: models.py
Class: UserContact (PascalCase)
Function: create_access_token (snake_case)
Constant: SECRET_KEY (UPPER_SNAKE_CASE)
```

---

## Import Order (PEP 8 Standard)

**Three-section pattern:**

1. **Standard library imports** (datetime, uuid, etc.)
2. **Third-party imports** (fastapi, sqlmodel, etc.)
3. **Local application imports** (app.core.config, app.models, etc.)

**Separate sections with blank lines.**

---

## Directory Organization Rules

**✅ DO:**
- Keep related functionality together (all auth logic in auth.py)
- Use `__init__.py` in every package directory
- Separate database models from API schemas
- Keep core utilities in core/ directory
- Version API endpoints (v1/, v2/ in future)

**❌ DON'T:**
- Mix database logic directly in API endpoint files
- Put business logic in main.py (only app initialization)
- Create circular imports between modules
- Store sensitive data in code (use .env)
- Hardcode configuration values

---

## Response Format Standards

**ALL API responses MUST use the envelope format:**

**Success:**
```
{
  "status": "success",
  "data": { ... },
  "message": "Optional message"
}
```

**Error:**
```
{
  "status": "error",
  "data": null,
  "message": "Error description"
}
```

**This ensures frontend can consistently parse all responses.**

---

## Database Relationship Summary

```
User (1) ─────────────< Contact (Many)
                           │
                           │ (1)
                           │
                           ├─────────< Memory (Many)
```

**Cascade Delete Behavior:**
- Delete User → Deletes all their Contacts → Deletes all Memories
- Delete Contact → Deletes all its Memories

---

## Authentication Flow Summary

```
1. User registers/logs in
2. Backend generates JWT with user_id in payload
3. Frontend stores JWT in localStorage
4. Frontend sends JWT in Authorization header for all protected requests
5. Backend validates JWT and extracts user_id
6. Backend uses user_id to filter database queries
7. Users can only access their own data
```

---

## CORS Configuration Requirements

**Backend MUST allow these origins:**
- `http://localhost:8080` (Vite dev server)
- `http://127.0.0.1:8080` (alternative localhost)

**Settings:**
- allow_credentials: True
- allow_methods: All (*)
- allow_headers: All (*)

**Without proper CORS, frontend cannot communicate with backend.**

---

## Key Architecture Principles

1. **Separation of Concerns:** Models ≠ Schemas ≠ Endpoints
2. **Dependency Injection:** Use FastAPI's Depends() for sessions and auth
3. **Type Safety:** Use type hints everywhere (UUID, str, datetime, etc.)
4. **Security First:** JWT validation on all protected routes, no raw SQL
5. **Consistent Responses:** Always use success/error envelope format
6. **UTC Timestamps:** Never use local timezone for created_at fields
7. **Data Isolation:** Users can only access their own contacts and memories

---

This structure ensures the backend codebase is clean, scalable, secure, and easy for AI code assistants to understand and work with.