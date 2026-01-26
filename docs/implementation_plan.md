# Implementation Plan
## GiftGenius Phase 1 - Step-by-Step Execution Guide

**Purpose:** This document provides a sequential, checkpoint-based plan to build the walking skeleton from zero to fully functional.

---

## Overview: The 5-Step Build Process

```
Step 1: Infrastructure (Docker)
   ↓
Step 2: Database Layer (Models)
   ↓
Step 3: Authentication (JWT + Security)
   ↓
Step 4: Core Features (Contacts + Memories)
   ↓
Step 5: Integration (Frontend ↔ Backend)
```

**Total Estimated Time:** 6-8 hours (for experienced developer)

---

## STEP 1: The Iron Skeleton (Infrastructure Setup)

**Goal:** Get Docker containers running with backend + database

### 1.1 Create Project Structure

```bash
mkdir giftgenius
cd giftgenius

# Create directory structure
mkdir -p backend/app/core backend/app/api/v1
touch backend/Dockerfile backend/requirements.txt backend/.dockerignore
touch backend/app/__init__.py backend/app/main.py backend/app/database.py
touch backend/app/core/__init__.py backend/app/core/config.py backend/app/core/security.py
touch backend/app/api/__init__.py backend/app/api/v1/__init__.py
touch .env .env.example .gitignore docker-compose.yml
```

### 1.2 Configure `.env`

```bash
# .env (create this first)
DATABASE_URL=postgresql://giftgenius_user:securepassword@db:5432/giftgenius
SECRET_KEY=09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
ENVIRONMENT=development
DEBUG=True
```

**Generate strong SECRET_KEY:**
```bash
openssl rand -hex 32
```

### 1.3 Create `docker-compose.yml`

Use the exact configuration from Backend Structure document (Section 3).

### 1.4 Create `backend/Dockerfile`

Use the exact Dockerfile from Backend Structure document (Section 4).

### 1.5 Create `backend/requirements.txt`

Use the exact requirements from Backend Structure document (Section 5).

### 1.6 Create Minimal `main.py`

```python
# backend/app/main.py
from fastapi import FastAPI

app = FastAPI(title="GiftGenius API")

@app.get("/")
def root():
    return {"message": "GiftGenius API is running"}
```

### 1.7 **CHECKPOINT 1: Test Infrastructure**

```bash
# From project root
docker-compose up --build
```

**Expected Output:**
```
✅ Database container starts (giftgenius-db)
✅ Backend container starts (giftgenius-backend)
✅ Backend shows: "Application startup complete"
✅ Visit http://localhost:8000 → See {"message": "GiftGenius API is running"}
✅ Visit http://localhost:8000/docs → See Swagger UI
```

**If this fails:**
- Check Docker is running
- Check .env file exists and has correct values
- Check no port conflicts (5432, 8000 already in use)

---

## STEP 2: The Data Layer (Database Models)

**Goal:** Define database schema and create tables

### 2.1 Create `database.py`

Use exact code from Backend Structure document (Section 8).

### 2.2 Create `models.py`

Use exact code from Backend Structure document (Section 9).

Key models:
- `User` (id, email, password_hash)
- `Contact` (id, name, relationship_type, birthday, user_id)
- `Memory` (id, content, contact_id)

### 2.3 Create `core/config.py`

Use exact code from Backend Structure document (Section 11).

### 2.4 Update `main.py` with Database Initialization

```python
# backend/app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import create_db_and_tables


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create database tables on startup"""
    print("🚀 Creating database tables...")
    create_db_and_tables()
    print("✅ Database ready")
    yield
    print("👋 Shutting down...")


app = FastAPI(
    title="GiftGenius API",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"status": "success", "data": {"message": "API is running"}}
```

### 2.5 **CHECKPOINT 2: Verify Database Tables**

```bash
# Restart containers
docker-compose down
docker-compose up --build
```

**Expected Logs:**
```
🚀 Creating database tables...
✅ Database ready
```

**Verify with Database Client:**

```bash
# Connect to database
docker exec -it giftgenius-db psql -U giftgenius_user -d giftgenius

# List tables
\dt

# Expected output:
 Schema |   Name    | Type  |      Owner      
--------|-----------|-------|------------------
 public | users     | table | giftgenius_user
 public | contacts  | table | giftgenius_user
 public | memories  | table | giftgenius_user

# Describe users table
\d users

# Exit
\q
```

**Alternative: Use DBeaver**
- Host: localhost
- Port: 5432
- Database: giftgenius
- Username: giftgenius_user
- Password: securepassword

---

## STEP 3: The Gatekeeper (Authentication)

**Goal:** Implement registration and login with JWT

### 3.1 Create `schemas.py`

Use exact code from Backend Structure document (Section 10).

Key schemas:
- `UserRegister`
- `UserLogin`
- `AuthResponse`
- `SuccessResponse`
- `ErrorResponse`

### 3.2 Create `core/security.py`

Use exact code from Backend Structure document (Section 12).

Key functions:
- `hash_password()`
- `verify_password()`
- `create_access_token()`
- `decode_token()`
- `get_current_user_id()` (dependency)

### 3.3 Create `api/v1/auth.py`

```python
"""
Authentication endpoints: register and login
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.database import get_session
from app.models import User
from app.schemas import (
    UserRegister,
    UserLogin,
    AuthResponse,
    UserResponse,
    SuccessResponse,
    ErrorResponse
)
from app.core.security import hash_password, verify_password, create_access_token


router = APIRouter()


@router.post("/register", response_model=SuccessResponse, status_code=status.HTTP_201_CREATED)
def register_user(
    user_data: UserRegister,
    session: Session = Depends(get_session)
):
    """
    Register a new user account.
    
    - Validates email uniqueness
    - Hashes password with Bcrypt
    - Returns JWT token
    """
    # Check if email already exists
    existing_user = session.exec(
        select(User).where(User.email == user_data.email)
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    new_user = User(
        email=user_data.email,
        password_hash=hash_password(user_data.password)
    )
    
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    
    # Generate JWT token
    access_token = create_access_token(new_user.id)
    
    return {
        "status": "success",
        "data": {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": str(new_user.id),
                "email": new_user.email
            }
        },
        "message": "Account created successfully"
    }


@router.post("/login", response_model=SuccessResponse)
def login_user(
    credentials: UserLogin,
    session: Session = Depends(get_session)
):
    """
    Authenticate user and return JWT token.
    
    - Verifies email and password
    - Returns JWT token valid for 24 hours
    """
    # Find user by email
    user = session.exec(
        select(User).where(User.email == credentials.email)
    ).first()
    
    # Verify user exists and password is correct
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Generate JWT token
    access_token = create_access_token(user.id)
    
    return {
        "status": "success",
        "data": {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": str(user.id),
                "email": user.email
            }
        },
        "message": "Login successful"
    }
```

### 3.4 Update `main.py` to Include Auth Router

```python
# Add this import at top
from app.api.v1 import auth

# Add this after CORS middleware
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
```

### 3.5 **CHECKPOINT 3: Test Authentication**

```bash
docker-compose restart backend
```

**Test Registration via Swagger UI** (`http://localhost:8000/docs`):

1. Open `/api/v1/auth/register` endpoint
2. Click "Try it out"
3. Enter:
```json
{
  "email": "test@example.com",
  "password": "SecurePass123"
}
```
4. Click "Execute"

**Expected Response (201):**
```json
{
  "status": "success",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "user": {
      "id": "uuid-here",
      "email": "test@example.com"
    }
  },
  "message": "Account created successfully"
}
```

**Test Login:**
1. Open `/api/v1/auth/login`
2. Try same credentials
3. Should receive token again

**Test Error Cases:**
- Register same email twice → 400 "Email already registered"
- Login with wrong password → 401 "Invalid email or password"

**Copy the `access_token` - you'll need it for next steps!**

---

## STEP 4: The Meat (Core Features)

**Goal:** Build CRUD endpoints for Contacts and Memories

### 4.1 Create `api/v1/contacts.py`

```python
"""
Contact management endpoints
"""

from typing import Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select, func

from app.database import get_session
from app.models import Contact, Memory
from app.schemas import (
    ContactCreate,
    ContactResponse,
    ContactListResponse,
    SuccessResponse
)
from app.core.security import get_current_user_id


router = APIRouter()


@router.post("", response_model=SuccessResponse, status_code=status.HTTP_201_CREATED)
def create_contact(
    contact_data: ContactCreate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: Session = Depends(get_session)
):
    """Create a new contact"""
    new_contact = Contact(
        **contact_data.model_dump(),
        user_id=user_id
    )
    
    session.add(new_contact)
    session.commit()
    session.refresh(new_contact)
    
    return {
        "status": "success",
        "data": {
            "id": str(new_contact.id),
            "name": new_contact.name,
            "relationship_type": new_contact.relationship_type,
            "birthday": new_contact.birthday.isoformat() if new_contact.birthday else None,
            "created_at": new_contact.created_at.isoformat()
        },
        "message": "Contact added successfully"
    }


@router.get("", response_model=SuccessResponse)
def list_contacts(
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: Session = Depends(get_session)
):
    """Get all contacts for authenticated user"""
    
    # Query contacts with memory count
    contacts = session.exec(
        select(Contact).where(Contact.user_id == user_id)
    ).all()
    
    # Build response with memory counts
    contacts_data = []
    for contact in contacts:
        memory_count = session.exec(
            select(func.count(Memory.id)).where(Memory.contact_id == contact.id)
        ).one()
        
        contacts_data.append({
            "id": str(contact.id),
            "name": contact.name,
            "relationship_type": contact.relationship_type,
            "birthday": contact.birthday.isoformat() if contact.birthday else None,
            "created_at": contact.created_at.isoformat(),
            "memory_count": memory_count
        })
    
    return {
        "status": "success",
        "data": {"contacts": contacts_data},
        "message": None
    }


@router.get("/{contact_id}", response_model=SuccessResponse)
def get_contact(
    contact_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: Session = Depends(get_session)
):
    """Get a specific contact"""
    contact = session.get(Contact, contact_id)
    
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found"
        )
    
    # Verify ownership
    if contact.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this contact"
        )
    
    return {
        "status": "success",
        "data": {
            "id": str(contact.id),
            "name": contact.name,
            "relationship_type": contact.relationship_type,
            "birthday": contact.birthday.isoformat() if contact.birthday else None,
            "created_at": contact.created_at.isoformat()
        },
        "message": None
    }


@router.delete("/{contact_id}", response_model=SuccessResponse)
def delete_contact(
    contact_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: Session = Depends(get_session)
):
    """Delete a contact (and all associated memories)"""
    contact = session.get(Contact, contact_id)
    
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found"
        )
    
    if contact.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this contact"
        )
    
    session.delete(contact)
    session.commit()
    
    return {
        "status": "success",
        "data": None,
        "message": "Contact deleted successfully"
    }
```

### 4.2 Create `api/v1/memories.py`

```python
"""
Memory management endpoints
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.database import get_session
from app.models import Contact, Memory
from app.schemas import (
    MemoryCreate,
    MemoryResponse,
    MemoryListResponse,
    SuccessResponse
)
from app.core.security import get_current_user_id


router = APIRouter()


@router.post("/{contact_id}/memories", response_model=SuccessResponse, status_code=status.HTTP_201_CREATED)
def create_memory(
    contact_id: uuid.UUID,
    memory_data: MemoryCreate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: Session = Depends(get_session)
):
    """Add a memory to a contact"""
    
    # Verify contact exists and belongs to user
    contact = session.get(Contact, contact_id)
    
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found"
        )
    
    if contact.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this contact"
        )
    
    # Create memory
    new_memory = Memory(
        content=memory_data.content,
        contact_id=contact_id
    )
    
    session.add(new_memory)
    session.commit()
    session.refresh(new_memory)
    
    return {
        "status": "success",
        "data": {
            "id": str(new_memory.id),
            "content": new_memory.content,
            "created_at": new_memory.created_at.isoformat()
        },
        "message": "Memory saved"
    }


@router.get("/{contact_id}/memories", response_model=SuccessResponse)
def list_memories(
    contact_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: Session = Depends(get_session)
):
    """Get all memories for a contact"""
    
    # Verify contact belongs to user
    contact = session.get(Contact, contact_id)
    
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found"
        )
    
    if contact.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this contact"
        )
    
    # Get memories sorted by newest first
    memories = session.exec(
        select(Memory)
        .where(Memory.contact_id == contact_id)
        .order_by(Memory.created_at.desc())
    ).all()
    
    memories_data = [
        {
            "id": str(memory.id),
            "content": memory.content,
            "created_at": memory.created_at.isoformat()
        }
        for memory in memories
    ]
    
    return {
        "status": "success",
        "data": {"memories": memories_data},
        "message": None
    }
```

### 4.3 Update `main.py` to Include New Routers

```python
# Add imports
from app.api.v1 import auth, contacts, memories

# Add routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(contacts.router, prefix="/api/v1/contacts", tags=["Contacts"])
app.include_router(memories.router, prefix="/api/v1/contacts", tags=["Memories"])
```

### 4.4 **CHECKPOINT 4: Test Complete API**

```bash
docker-compose restart backend
```

**Full User Journey Test in Swagger UI:**

1. **Register**: `/api/v1/auth/register` → Get token
2. **Authorize**: Click "Authorize" button (🔒) → Paste token
3. **Create Contact**: `POST /api/v1/contacts`
```json
{
  "name": "Amy Chen",
  "relationship_type": "Friend",
  "birthday": "1995-10-20"
}
```
4. **List Contacts**: `GET /api/v1/contacts` → See Amy
5. **Add Memory**: `POST /api/v1/contacts/{contact_id}/memories`
```json
{
  "content": "Loves matcha lattes from Blue Bottle"
}
```
6. **Get Memories**: `GET /api/v1/contacts/{contact_id}/memories` → See the memory

**All endpoints should return 200/201 with proper `status: success` envelope!**

---

## STEP 5: The Handshake (Frontend Integration)

**Goal:** Connect React frontend to Python backend

### 5.1 Verify Frontend Configuration

**Check `frontend/src/api/client.js` (or similar):**

```javascript
import axios from 'axios';

const client = axios.create({
  baseURL: 'http://localhost:8000/api/v1',  // ✅ Must match backend
  headers: {
    'Content-Type': 'application/json'
  }
});

// Add token to every request
client.interceptors.request.use(config => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle errors globally
client.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      localStorage.clear();
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default client;
```

### 5.2 Start Frontend Dev Server

```bash
cd frontend
npm install  # If first time
npm run dev
```

**Expected:** Frontend runs on `http://localhost:5173`

### 5.3 Verify CORS is Working

**Open browser console (F12) on frontend:**

Try to register from the UI. If you see:
```
Access-Control-Allow-Origin error
```

Then CORS is not configured correctly. Go back to `backend/app/main.py` and verify:
```python
allow_origins=["http://localhost:5173"]
```

### 5.4 **CHECKPOINT 5: End-to-End Test**

**Complete User Flow:**

1. ✅ Open `http://localhost:5173`
2. ✅ Click "Sign Up" → Enter email/password → Submit
3. ✅ Should redirect to Dashboard
4. ✅ Click "+" FAB → Enter "Amy Chen", "Friend", birthday
5. ✅ Click Save → Contact card appears
6. ✅ Click on Amy's card → Opens profile page
7. ✅ Type "Loves matcha tea" → Click "Add Note"
8. ✅ Memory appears in feed below
9. ✅ Add 2-3 more memories
10. ✅ Logout → Login again → Data persists

**If ALL steps work: 🎉 Phase 1 Complete!**

---

## Common Issues & Solutions

### Issue: Docker containers won't start

**Solution:**
```bash
# Clean everything
docker-compose down -v
docker system prune -a
docker-compose up --build
```

### Issue: Database tables not created

**Solution:**
```bash
# Check logs
docker logs giftgenius-backend

# Manually create tables
docker exec -it giftgenius-backend python -c "from app.database import create_db_and_tables; create_db_and_tables()"
```

### Issue: 401 Unauthorized on every request

**Check:**
1. Token is being sent in Authorization header
2. SECRET_KEY in .env matches what generated the token
3. Token hasn't expired (24 hours)

**Debug:**
```python
# Add logging in security.py decode_token()
print(f"Token: {token}")
print(f"Decoded: {payload}")
```

### Issue: Frontend can't connect to backend

**Check:**
1. Backend is running on port 8000
2. Frontend baseURL is `http://localhost:8000/api/v1`
3. CORS allows `http://localhost:5173`
4. No browser ad-blocker blocking requests

### Issue: Passwords not hashing

**Check:**
```bash
# In Python shell
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
hashed = pwd_context.hash("test123")
print(hashed)  # Should start with $2b$
```

---

## Post-Implementation Checklist

Before marking Phase 1 as "Done":

- [ ] All 5 checkpoints passed
- [ ] Database persists data after `docker-compose down && docker-compose up`
- [ ] User can register, login, and access protected routes
- [ ] Contacts CRUD fully functional via Swagger UI
- [ ] Memories CRUD fully functional via Swagger UI
- [ ] Frontend successfully integrates (login → dashboard → add contact → add memory)
- [ ] Error handling works (invalid login, missing token, etc.)
- [ ] CORS configured correctly
- [ ] `.env` file in `.gitignore`
- [ ] Code follows structure defined in Backend Structure doc
- [ ] All responses follow envelope format (status, data, message)

---

## Next Steps (Phase 2 Preview)

Once Phase 1 is stable:

1. **Add Alembic** for database migrations
2. **Add Tests** (pytest for backend, Vitest for frontend)
3. **Add LangGraph** for AI gift generation
4. **Deploy to Cloud** (Railway, Render, or AWS)
5. **Add Advanced Features** (search, tags, image uploads)

---

## Time Estimates (Per Step)

| Step | Task | Estimated Time |
|------|------|----------------|
| 1 | Infrastructure Setup | 1 hour |
| 2 | Database Models | 1 hour |
| 3 | Authentication | 2 hours |
| 4 | Core Features (Contacts + Memories) | 2 hours |
| 5 | Frontend Integration | 1 hour |
| **Total** | | **6-8 hours** |

---

## Success Metrics

**You've successfully completed Phase 1 when:**

✅ A user can create an account  
✅ A user can login and receive a JWT token  
✅ A user can add 5 contacts  
✅ A user can add 20+ memories across contacts  
✅ Data persists across sessions  
✅ Frontend and Backend communicate without errors  
✅ All API endpoints return proper response envelopes  
✅ No console errors in browser or terminal  

**Congratulations! You now have a solid foundation for Phase 2.** 🚀