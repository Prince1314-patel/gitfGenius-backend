# Frontend Guidelines Document
## GiftGenius - Backend Integration Specifications

**Purpose:** This document defines the exact API contract the Backend must implement to integrate seamlessly with the already-built Frontend.

---

## Critical Integration Rules

### 🚨 NON-NEGOTIABLE REQUIREMENTS

1. **Base URL:** All endpoints MUST be prefixed with `/api/v1`
2. **Response Format:** ALL responses must use the standard envelope (see below)
3. **Authentication:** Protected routes MUST validate `Authorization: Bearer <token>` header
4. **CORS:** Backend MUST allow `http://localhost:5173` (Vite dev server)
5. **Content-Type:** All requests/responses use `application/json`

---

## API Response Envelope (STRICT CONTRACT)

### Success Response Format

**ALL successful responses MUST follow this structure:**

```json
{
  "status": "success",
  "data": {
    // The actual payload goes here
  },
  "message": "Optional user-facing message for toast notifications"
}
```

**Example - Login Success:**
```json
{
  "status": "success",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "user": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "email": "user@example.com"
    }
  },
  "message": "Login successful"
}
```

**Example - Get Contacts:**
```json
{
  "status": "success",
  "data": {
    "contacts": [
      {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "name": "Amy Chen",
        "relationship_type": "Friend",
        "birthday": "1995-10-20",
        "created_at": "2026-01-26T10:30:00Z",
        "memory_count": 12
      }
    ]
  },
  "message": null
}
```

---

### Error Response Format

**ALL error responses MUST follow this structure:**

```json
{
  "status": "error",
  "data": null,
  "message": "Human-readable error description"
}
```

**Example - Validation Error:**
```json
{
  "status": "error",
  "data": null,
  "message": "Email is required"
}
```

**Example - Authentication Error:**
```json
{
  "status": "error",
  "data": null,
  "message": "Invalid credentials"
}
```

**Example - Not Found:**
```json
{
  "status": "error",
  "data": null,
  "message": "Contact not found"
}
```

---

## HTTP Status Codes (Frontend Expectations)

The Frontend is configured to handle these status codes:

| Status Code | Meaning | Frontend Action |
|-------------|---------|-----------------|
| **200** | Success (GET, PUT, DELETE) | Parse `data` field |
| **201** | Created (POST) | Parse `data` field, show success toast |
| **400** | Bad Request | Show `message` in toast (red) |
| **401** | Unauthorized | Clear localStorage, redirect to `/login` |
| **404** | Not Found | Show `message` in toast |
| **422** | Validation Error | Show `message` in toast (Pydantic errors) |
| **500** | Server Error | Show "Server error, please try again" |

---

## Authentication Flow (Frontend Behavior)

### Registration

**Frontend Sends:**
```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "email": "newuser@example.com",
  "password": "SecurePass123!"
}
```

**Backend MUST Return (201):**
```json
{
  "status": "success",
  "data": {
    "access_token": "eyJhbGc...",
    "token_type": "bearer",
    "user": {
      "id": "uuid-here",
      "email": "newuser@example.com"
    }
  },
  "message": "Account created successfully"
}
```

**Frontend Will:**
1. Store `access_token` in `localStorage.setItem('token', data.access_token)`
2. Store `user` object in `localStorage.setItem('user', JSON.stringify(data.user))`
3. Set Axios default header: `Authorization: Bearer <token>`
4. Redirect to `/dashboard`
5. Show toast with `message` value

---

### Login

**Frontend Sends:**
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Backend MUST Return (200):**
```json
{
  "status": "success",
  "data": {
    "access_token": "eyJhbGc...",
    "token_type": "bearer",
    "user": {
      "id": "uuid-here",
      "email": "user@example.com"
    }
  },
  "message": "Welcome back!"
}
```

**On Error (401):**
```json
{
  "status": "error",
  "data": null,
  "message": "Invalid email or password"
}
```

---

### Token Usage in Protected Requests

**Every protected request includes:**
```http
GET /api/v1/contacts
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
```

**Backend MUST:**
1. Extract token from `Authorization` header
2. Verify JWT signature
3. Extract `user_id` from token payload
4. Use `user_id` to filter data (e.g., only return user's own contacts)
5. Return 401 if token is missing, invalid, or expired

---

## Contact Management Endpoints

### 1. Get All Contacts

**Request:**
```http
GET /api/v1/contacts
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "status": "success",
  "data": {
    "contacts": [
      {
        "id": "uuid-1",
        "name": "Amy Chen",
        "relationship_type": "Friend",
        "birthday": "1995-10-20",
        "created_at": "2026-01-15T10:00:00Z",
        "memory_count": 12
      },
      {
        "id": "uuid-2",
        "name": "Bob Miller",
        "relationship_type": "Colleague",
        "birthday": "1988-03-15",
        "created_at": "2026-01-20T14:30:00Z",
        "memory_count": 5
      }
    ]
  },
  "message": null
}
```

**Frontend Expects:**
- `contacts` array (can be empty `[]`)
- Each contact has `id`, `name`, `relationship_type`, `birthday`, `created_at`
- Optional: `memory_count` (if backend counts memories per contact)

---

### 2. Create Contact

**Request:**
```http
POST /api/v1/contacts
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Carol Lee",
  "relationship_type": "Sister",
  "birthday": "1992-07-08"
}
```

**Response (201):**
```json
{
  "status": "success",
  "data": {
    "id": "new-uuid",
    "name": "Carol Lee",
    "relationship_type": "Sister",
    "birthday": "1992-07-08",
    "created_at": "2026-01-26T15:45:00Z"
  },
  "message": "Contact added successfully"
}
```

**Validation Errors (400):**
```json
{
  "status": "error",
  "data": null,
  "message": "Name is required"
}
```

**Frontend Form Validation (Before Sending):**
- Name: Required, 1-100 characters
- Relationship Type: Required, one of: Friend, Family, Colleague, Partner, Other
- Birthday: Optional, valid ISO date format (YYYY-MM-DD)

---

### 3. Get Single Contact

**Request:**
```http
GET /api/v1/contacts/{contact_id}
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "status": "success",
  "data": {
    "id": "uuid-1",
    "name": "Amy Chen",
    "relationship_type": "Friend",
    "birthday": "1995-10-20",
    "created_at": "2026-01-15T10:00:00Z"
  },
  "message": null
}
```

**Error - Not Found (404):**
```json
{
  "status": "error",
  "data": null,
  "message": "Contact not found"
}
```

**Error - Unauthorized Access (403):**
```json
{
  "status": "error",
  "data": null,
  "message": "You don't have access to this contact"
}
```

---

### 4. Delete Contact

**Request:**
```http
DELETE /api/v1/contacts/{contact_id}
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "status": "success",
  "data": null,
  "message": "Contact deleted successfully"
}
```

**Frontend Behavior:**
1. Shows confirmation modal first
2. On confirm, sends DELETE request
3. On success, removes contact card from UI
4. Shows success toast with `message`

---

## Memory Management Endpoints

### 1. Get Memories for Contact

**Request:**
```http
GET /api/v1/contacts/{contact_id}/memories
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "status": "success",
  "data": {
    "memories": [
      {
        "id": "memory-uuid-1",
        "content": "Loves matcha lattes, especially from Blue Bottle.",
        "created_at": "2026-01-26T14:22:00Z"
      },
      {
        "id": "memory-uuid-2",
        "content": "Mentioned wanting to visit Japan in spring.",
        "created_at": "2026-01-25T09:15:00Z"
      }
    ]
  },
  "message": null
}
```

**Frontend Expects:**
- `memories` array sorted by `created_at` DESC (newest first)
- Can be empty array `[]` if no memories yet
- Each memory has `id`, `content`, `created_at`

---

### 2. Add Memory to Contact

**Request:**
```http
POST /api/v1/contacts/{contact_id}/memories
Authorization: Bearer <token>
Content-Type: application/json

{
  "content": "Allergic to shellfish - important for restaurant choices!"
}
```

**Response (201):**
```json
{
  "status": "success",
  "data": {
    "id": "new-memory-uuid",
    "content": "Allergic to shellfish - important for restaurant choices!",
    "created_at": "2026-01-26T16:30:00Z"
  },
  "message": "Memory saved"
}
```

**Validation Error (400):**
```json
{
  "status": "error",
  "data": null,
  "message": "Memory content cannot be empty"
}
```

**Frontend Behavior:**
1. User types in text area
2. Clicks "Add Note" or presses Enter
3. Sends POST request
4. On success: Clears input, prepends new memory to list
5. Shows timestamp as "Just now" → "5 minutes ago" → etc.

---

## Frontend Error Handling (What Backend Must Support)

### Axios Interceptor Pattern

The Frontend has this error handler:

```javascript
// src/api/client.js (already implemented)
axios.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid
      localStorage.clear();
      window.location.href = '/login';
    }
    
    // Show error message to user
    const message = error.response?.data?.message || 'Something went wrong';
    toast.error(message);
    
    return Promise.reject(error);
  }
);
```

**Backend Must Ensure:**
- All 401 responses include proper error message
- All 4xx/5xx responses follow error envelope format
- Never return HTML error pages (only JSON)

---

## CORS Configuration (Backend Requirement)

**Backend MUST allow:**

```python
# In main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://127.0.0.1:5173"   # Alternative localhost
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)
```

**Without this, Frontend will get CORS errors in browser console.**

---

## Date/Time Format Standards

**All dates MUST use ISO 8601 format:**

- **Date only:** `"1995-10-20"` (for birthdays)
- **DateTime with timezone:** `"2026-01-26T14:22:00Z"` (for created_at)

**Frontend will:**
- Send birthdays as `YYYY-MM-DD`
- Display created_at as relative time ("2 hours ago")
- Use `date-fns` library for formatting

---

## Relationship Type Enum

**Backend MUST accept these exact values:**

```python
# In schemas.py or models.py
from enum import Enum

class RelationshipType(str, Enum):
    FRIEND = "Friend"
    FAMILY = "Family"
    COLLEAGUE = "Colleague"
    PARTNER = "Partner"
    OTHER = "Other"
```

**Frontend dropdown shows:** Friend, Family, Colleague, Partner, Other

---

## UUID Format

**All IDs MUST be UUID v4:**

```python
import uuid

# Example
id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
```

**Frontend sends UUIDs as strings in URLs:**
```
/api/v1/contacts/550e8400-e29b-41d4-a716-446655440000
```

**Backend must parse and validate UUIDs properly.**

---

## Empty State Responses

**When user has no contacts:**

```json
{
  "status": "success",
  "data": {
    "contacts": []
  },
  "message": null
}
```

**When contact has no memories:**

```json
{
  "status": "success",
  "data": {
    "memories": []
  },
  "message": null
}
```

**Frontend will show empty state UI with illustrations and CTAs.**

---

## Pagination (NOT in Phase 1)

Phase 1 returns ALL data (no pagination).

**Future Phase 2:**
```json
{
  "status": "success",
  "data": {
    "contacts": [...],
    "pagination": {
      "page": 1,
      "per_page": 20,
      "total": 45,
      "total_pages": 3
    }
  }
}
```

---

## Field Validation Rules (Backend Must Enforce)

### User Registration
```python
{
  "email": str,      # Required, valid email format, unique
  "password": str    # Required, min 8 chars (frontend validates, backend enforces)
}
```

### Contact Creation
```python
{
  "name": str,                    # Required, 1-100 chars
  "relationship_type": str,       # Required, must be in enum
  "birthday": date | None         # Optional, valid ISO date if provided
}
```

### Memory Creation
```python
{
  "content": str   # Required, 1-5000 chars (prevents spam)
}
```

---

## Testing Checklist for Backend Developer

Before marking an endpoint as "done", verify:

- [ ] Response follows envelope format exactly
- [ ] Proper HTTP status code returned
- [ ] CORS headers present
- [ ] JWT validation works (401 for invalid token)
- [ ] User can only access their own data
- [ ] Error messages are user-friendly (not stack traces)
- [ ] Timestamps in ISO 8601 with UTC timezone
- [ ] UUIDs returned as strings in JSON
- [ ] Empty arrays returned (not null) for empty lists
- [ ] Swagger UI documentation auto-generated and accurate

---

## API Documentation URL

**Once backend is running:**

Interactive Docs: `http://localhost:8000/docs`

**Frontend developers can test endpoints directly in Swagger UI before connecting the React app.**

---

## Critical "Don't Break" Rules

🚨 **The Frontend assumes these are ALWAYS true:**

1. ✅ `status` field is always present ("success" or "error")
2. ✅ `data` field is present (object for success, null for error)
3. ✅ `message` field is present (string or null)
4. ✅ 401 always means "redirect to login"
5. ✅ All dates are ISO 8601 strings
6. ✅ All IDs are UUID strings
7. ✅ Arrays are never null (use `[]` for empty)

**If these rules are broken, the Frontend will crash or behave unpredictably.**

---

This document is the **contract** between Frontend and Backend. Treat it as law during implementation.