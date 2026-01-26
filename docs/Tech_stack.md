# Tech Stack Document
## GiftGenius - Technology Architecture & Decisions

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                     User Browser                         │
│                  (Chrome, Firefox, etc.)                 │
└────────────────────────┬────────────────────────────────┘
                         │ HTTP/HTTPS
                         ↓
┌─────────────────────────────────────────────────────────┐
│                  Frontend Container                      │
│              React + Vite (Port 8080)                    │
│                   [ALREADY BUILT]                        │
└────────────────────────┬────────────────────────────────┘
                         │ REST API (JSON)
                         ↓
┌─────────────────────────────────────────────────────────┐
│                  Backend Container                       │
│             FastAPI + Python (Port 8000)                 │
│                   [TO BE BUILT]                          │
└────────────────────────┬────────────────────────────────┘
                         │ SQL Queries
                         ↓
┌─────────────────────────────────────────────────────────┐
│                 Database Container                       │
│              PostgreSQL 15 (Port 5432)                   │
└─────────────────────────────────────────────────────────┘
```

---

## Infrastructure Layer

### Containerization

**Docker**
- Version: 20.10+
- Purpose: Isolate services, ensure consistency across environments
- Configuration: `docker-compose.yml` at project root

**Docker Compose**
- Version: 3.8
- Services: `backend`, `database`
- Networks: Single bridge network for inter-service communication
- Volumes: Persistent storage for Postgres data

**Environment Management**
- File: `.env` (git-ignored)
- Purpose: Store secrets, database URLs, JWT keys
- Pattern: `KEY=value` format
- Required Variables:
  ```
  DATABASE_URL=postgresql://user:password@db:5432/giftgenius
  SECRET_KEY=your-secret-key-min-32-chars
  ALGORITHM=HS256
  ACCESS_TOKEN_EXPIRE_MINUTES=1440
  ```

---

## Database Layer

### PostgreSQL 15

**Why PostgreSQL?**
- ✅ Strong ACID compliance for data integrity
- ✅ Excellent support for relational data (User → Contacts → Memories)
- ✅ JSON support for future flexibility
- ✅ Mature, battle-tested, free and open-source

**Configuration:**
- Image: `postgres:15-alpine` (smaller footprint)
- Port: `5432` (internal), not exposed externally in production
- Database Name: `giftgenius`
- Character Set: UTF-8
- Timezone: UTC

**Data Persistence:**
- Docker Volume: `postgres_data`
- Survives container restarts
- Backup strategy: (Future) `pg_dump` nightly

**Connection Pooling:**
- Handled by SQLModel/SQLAlchemy
- Default pool size: 5 connections
- Max overflow: 10

---

## Backend Layer (BUILD TARGET)

### Language: Python 3.10+

**Why Python?**
- ✅ Excellent for rapid development
- ✅ Rich ecosystem for AI/ML (future LangGraph integration)
- ✅ FastAPI provides async performance
- ✅ Strong typing with Pydantic

**Version:** 3.10.x or higher (for match-case and type hints)

---

### Framework: FastAPI

**Version:** 0.104+

**Why FastAPI?**
- ✅ Automatic API documentation (Swagger UI)
- ✅ Async support for high concurrency
- ✅ Built-in data validation with Pydantic
- ✅ Modern Python type hints
- ✅ Fastest Python web framework

**Key Features Used:**
- Path operations (routers)
- Dependency injection (auth validation)
- Request/Response models
- Exception handlers
- CORS middleware
- Lifespan events (startup/shutdown)

**API Conventions:**
- RESTful design
- Versioned URLs: `/api/v1/*`
- JSON request/response bodies
- HTTP status codes follow standards

---

### ORM: SQLModel

**Version:** 0.0.14+

**Why SQLModel?**
- ✅ Combines SQLAlchemy (ORM) + Pydantic (validation)
- ✅ Single model definition for DB and API
- ✅ Type-safe queries
- ✅ Created by FastAPI author (seamless integration)

**Usage Pattern:**
```python
# Single class serves as both DB table and Pydantic model
class Contact(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str
    user_id: uuid.UUID = Field(foreign_key="user.id")
```

**Migration Strategy (Phase 1):**
- No Alembic initially (speed over perfection)
- Use `SQLModel.metadata.create_all(engine)` on startup
- Alembic added in Phase 2 for schema migrations

---

### Authentication Stack

**JWT (JSON Web Tokens)**
- Library: `python-jose[cryptography]`
- Algorithm: HS256 (symmetric signing)
- Token Expiry: 24 hours (1440 minutes)
- Payload: `{"sub": user_id, "exp": timestamp}`
- Storage: Frontend localStorage (not httpOnly cookies in Phase 1)

**Password Hashing**
- Library: `passlib[bcrypt]`
- Algorithm: Bcrypt
- Rounds: 12 (default, good balance of security/speed)
- Salt: Auto-generated per password

**Security Flow:**
```
Register: plaintext password → bcrypt hash → store in DB
Login: plaintext password → bcrypt verify against hash → generate JWT
Protected Route: JWT from header → verify signature → extract user_id
```

---

### Dependencies (requirements.txt)

```
# Core Framework
fastapi==0.104.1
uvicorn[standard]==0.24.0  # ASGI server

# Database
sqlmodel==0.0.14
psycopg2-binary==2.9.9  # PostgreSQL adapter

# Authentication
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4

# Utilities
python-dotenv==1.0.0  # .env file loading
pydantic==2.5.0  # (included with FastAPI)
pydantic-settings==2.1.0
```

---

## Frontend Layer (ALREADY BUILT)

### Framework: React 18

**Build Tool:** Vite 5
- Why: Lightning-fast HMR, modern build tool
- Dev Server: `localhost:8080`
- Production Build: Optimized static files

### Styling: Tailwind CSS

**Version:** 3.x

**Theme Customization:**
```javascript
// tailwind.config.js (already configured)
colors: {
  coral: {
    50: '#fff5f3',
    500: '#ff6b6b',  // Primary CTA
    600: '#ee5a52'
  },
  teal: {
    50: '#f0fdfa',
    500: '#14b8a6',  // Accent
    600: '#0d9488'
  }
}
```

**Design System:**
- Buttons: Coral for primary, Teal for secondary
- Cards: White with subtle shadows
- Inputs: Teal focus rings
- Spacing: 4px base unit (Tailwind default)

---

### State Management

**Pattern:** React Context + Local State

**Why no Redux?**
- ✅ App is simple enough for Context
- ✅ Avoids boilerplate
- ✅ Most state is server-driven (fetch on load)

**Context Structure:**
```javascript
AuthContext:
  - token
  - user
  - login()
  - logout()
  
ContactsContext:
  - contacts[]
  - addContact()
  - deleteContact()
```

---

### HTTP Client: Axios

**Version:** 1.6+

**Configuration:**
```javascript
// src/api/client.js (must be updated)
const client = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json'
  }
});

// Interceptor adds token to every request
client.interceptors.request.use(config => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
```

---

## Development Tools

### Code Quality

**Linter (Backend):**
- `ruff` or `flake8` (optional, not blocking)
- Enforce: max line length 100, no unused imports

**Formatter (Backend):**
- `black` (optional)
- Config: 100 char line length

**Type Checking (Backend):**
- `mypy` (optional, recommended for Phase 2)

---

### Database Tools

**GUI Client:**
- DBeaver (recommended, free)
- PgAdmin 4 (alternative)
- Purpose: Inspect tables, run manual queries during dev

**CLI Access:**
```bash
docker exec -it giftgenius-db psql -U giftgenius_user -d giftgenius
```

---

### API Testing

**Interactive Docs:**
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- Auto-generated by FastAPI

**Manual Testing:**
- Postman (optional)
- cURL (for quick tests)
- Browser DevTools Network tab

---

## Communication Protocols

### REST API Design

**Endpoint Naming:**
```
GET    /api/v1/contacts          # List all
POST   /api/v1/contacts          # Create one
GET    /api/v1/contacts/{id}     # Get one
DELETE /api/v1/contacts/{id}     # Delete one

GET    /api/v1/contacts/{id}/memories      # List memories
POST   /api/v1/contacts/{id}/memories      # Add memory
```

**Response Envelope (Mandatory):**
```json
{
  "status": "success" | "error",
  "data": { ... } | null,
  "message": "Optional human message"
}
```

**HTTP Status Codes:**
- 200: Success (GET, DELETE)
- 201: Created (POST)
- 400: Bad Request (validation failed)
- 401: Unauthorized (missing/invalid token)
- 404: Not Found
- 500: Server Error

---

## Security Considerations

**CORS Configuration:**
```python
# main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**SQL Injection Prevention:**
- ✅ SQLModel ORM (parameterized queries)
- ❌ Never use f-strings for SQL

**JWT Security:**
- ✅ Short expiry (24h)
- ✅ Secret key in .env (not hardcoded)
- ❌ No refresh tokens in Phase 1 (add later)

**Password Security:**
- ✅ Bcrypt hashing
- ✅ Minimum 8 characters (frontend validation)
- ❌ No password reset in Phase 1

---

## Deployment Strategy (Phase 1)

**Local Development:**
```bash
docker-compose up --build
```

**Services Start Order:**
1. Database (health check: accepts connections)
2. Backend (depends_on: database)
3. Frontend (dev server, not containerized yet)

**Ports:**
- Frontend: 8080 (Vite dev server)
- Backend: 8000 (FastAPI)
- Database: 5432 (internal only)

**Future (Phase 2):**
- Production: Railway, Render, or AWS ECS
- Frontend: Vercel or Netlify
- Database: Managed Postgres (AWS RDS, Supabase)

---

## Version Control

**Git Strategy:**
- Main branch: production-ready
- Feature branches: `feature/auth-endpoints`
- Commits: Conventional Commits format

**.gitignore Must Include:**
```
.env
__pycache__/
*.pyc
postgres_data/
node_modules/
.vite/
```

---

## Performance Targets

**API Response Times:**
- Auth endpoints: < 500ms (bcrypt is slow)
- CRUD operations: < 200ms
- List queries: < 300ms (with 100 contacts)

**Database Indexes (Future):**
```sql
CREATE INDEX idx_contacts_user_id ON contacts(user_id);
CREATE INDEX idx_memories_contact_id ON memories(contact_id);
```

---

## Monitoring & Logging

**Phase 1 (Simple):**
- Console logs in backend (`print()` acceptable for now)
- Frontend: Browser console
- Database: Postgres logs in Docker

**Phase 2 (Improved):**
- Python `logging` module
- Log levels: DEBUG, INFO, WARNING, ERROR
- Structured logs (JSON format)

---

## Technology Decision Matrix

| Requirement | Chosen Tech | Alternatives Considered | Why Chosen |
|-------------|-------------|------------------------|------------|
| Backend Framework | FastAPI | Django, Flask | Auto docs, async, modern |
| Database | PostgreSQL | MySQL, MongoDB | Relational integrity, maturity |
| ORM | SQLModel | SQLAlchemy, Django ORM | Type safety, Pydantic integration |
| Auth | JWT + Bcrypt | OAuth, Session cookies | Stateless, simple for MVP |
| Container | Docker | Kubernetes, Bare metal | Portability, reproducibility |
| Frontend (given) | React + Vite | Next.js, Vue | Already built, fast dev server |

---

## Future Tech Additions (Post Phase 1)

**Phase 2:**
- Alembic (database migrations)
- Redis (caching, session storage)
- Celery (background tasks)
- LangGraph (AI agent workflows)

**Phase 3:**
- Monitoring: Sentry, DataDog
- CDN: CloudFlare
- File storage: AWS S3

---

This tech stack is optimized for rapid development while maintaining production-grade architecture patterns.