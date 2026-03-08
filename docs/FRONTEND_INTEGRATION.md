# GiftGenius Backend – Frontend Integration Guide

This document gives frontend developers everything needed to integrate with the GiftGenius API in one shot: base URL, authentication, all endpoints, request/response shapes, error handling, and copy-paste examples.

---

## Table of Contents

1. [Quick Reference](#1-quick-reference)
2. [Environment & Base URL](#2-environment--base-url)
3. [CORS](#3-cors)
4. [Response Envelope](#4-response-envelope)
5. [Authentication](#5-authentication)
6. [API Endpoints](#6-api-endpoints)
7. [Error Handling](#7-error-handling)
8. [Validation Rules](#8-validation-rules)
9. [Code Examples](#9-code-examples)
10. [Integration Checklist](#10-integration-checklist)

---

## 1. Quick Reference

| Item | Value |
|------|--------|
| **Base URL (local)** | `http://localhost:8000` |
| **API prefix** | `/api/v1` |
| **Auth** | Bearer JWT in `Authorization` header |
| **Content-Type** | `application/json` |
| **Token expiry** | 24 hours |
| **Interactive docs** | `http://localhost:8000/docs` (Swagger), `http://localhost:8000/redoc` (ReDoc) |

---

## 2. Environment & Base URL

**Best practice:** Store the API base URL in environment variables so you can switch between local and production without code changes.

**Example `.env` (frontend):**

```env
VITE_API_BASE_URL=http://localhost:8000
# or for production:
# VITE_API_BASE_URL=https://api.your-giftgenius-domain.com
```

**Usage (Vite/React):**

```javascript
const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const API_V1 = `${API_BASE}/api/v1`;
```

Use `API_V1` for all API calls below (e.g. `${API_V1}/auth/login`).

---

## 3. CORS

The backend allows:

- **Origins:** `http://localhost:8080`, `http://127.0.0.1:8080`
- **Credentials:** `true` (cookies/auth headers allowed)
- **Methods:** all
- **Headers:** all

If your frontend runs on a different origin (e.g. `http://localhost:3000`), the backend team must add it to `allow_origins` in `app/main.py`. For local dev, use `http://localhost:8080` or `http://127.0.0.1:8080` to avoid CORS issues.

Browsers send `Origin` automatically; no extra headers are required for preflight.

---

## 4. Response Envelope

Every response uses the same envelope. **Always read `status` first**, then `data` or `message`/`error_code`/`details`.

### Success

```json
{
  "status": "success",
  "data": { ... },
  "message": "Optional human-readable message"
}
```

- `data`: payload (object or array); can be `null` for some success responses (e.g. delete).
- `message`: optional; may be empty string for list/get.

### Error

```json
{
  "status": "error",
  "data": null,
  "message": "Human-readable error message",
  "error_code": "ERROR_CODE",
  "details": { ... }
}
```

- `error_code`: stable string for programmatic handling (see [Error codes](#72-error-codes)).
- `details`: optional; for validation errors it contains `field_errors` (see [Validation errors](#73-validation-errors)).

**Rule:** Check `response.status === "success"` (or `"error"`) and then use `data` or `message`/`error_code`/`details` accordingly. Do not rely only on HTTP status code for the envelope shape.

---

## 5. Authentication

### 5.1 Flow

1. **Register:** `POST /api/v1/auth/register` with `email`, `password`, optional `full_name` → returns `user` + `access_token`.
2. **Login:** `POST /api/v1/auth/login` with `email`, `password` → returns `user` + `access_token`.
3. **Protected routes:** Send header: `Authorization: Bearer <access_token>`.
4. **Token expiry:** Tokens expire after 24 hours. On 401 with `error_code: "TOKEN_EXPIRED"` or `"INVALID_TOKEN"`, redirect to login and clear stored token.

### 5.2 Storing the token

- Store `access_token` in memory, `localStorage`, or a secure cookie after login/register.
- Send it on every request to protected endpoints: `Authorization: Bearer <access_token>`.
- Do **not** send the token to public endpoints (`/`, `/health`, `/api/v1/auth/register`, `/api/v1/auth/login`).

### 5.3 Logout

- Backend has no logout endpoint; logout is client-side: delete the stored token and (optionally) clear user state.

---

## 6. API Endpoints

All request bodies must be JSON (`Content-Type: application/json`). Path parameters are UUIDs unless noted.

---

### 6.1 Public (no auth)

#### `GET /`

Health / API status.

**Response (200):**

```json
{
  "status": "success",
  "data": {
    "message": "GiftGenius API is running",
    "version": "1.0.0",
    "environment": "development"
  }
}
```

#### `GET /health`

Health check including database.

**Response (200):**

```json
{
  "status": "success",
  "data": {
    "api": "healthy",
    "database": "connected",
    "environment": "development"
  }
}
```

---

### 6.2 Auth

#### `POST /api/v1/auth/register`

Register a new user.

**Request body:**

| Field | Type | Required | Rules |
|-------|------|----------|--------|
| `email` | string | Yes | Valid email format |
| `password` | string | Yes | Min 8 characters |
| `full_name` | string | No | Max 100 chars; default `""` |

**Response (200):**

```json
{
  "status": "success",
  "data": {
    "user": {
      "id": "uuid-string",
      "email": "user@example.com",
      "full_name": "Jane Doe",
      "created_at": "2026-03-08T12:00:00.000000"
    },
    "access_token": "eyJ...",
    "token_type": "bearer"
  },
  "message": "User registered successfully."
}
```

**Errors:**

- **400** – Validation (invalid email, short password, missing fields). Body includes `error_code: "VALIDATION_ERROR"` and `details.field_errors`.
- **409** – Email already exists. Body includes `error_code: "DUPLICATE_EMAIL"`.
- **500** – `error_code: "SYSTEM_ERROR"`.

---

#### `POST /api/v1/auth/login`

Log in.

**Request body:**

| Field | Type | Required |
|-------|------|----------|
| `email` | string | Yes |
| `password` | string | Yes |

**Response (200):** Same shape as register `data` (user + `access_token` + `token_type`).

**Errors:**

- **400** – Validation (e.g. missing email/password). `error_code: "VALIDATION_ERROR"`.
- **401** – Invalid email or password. `error_code: "INVALID_CREDENTIALS"`. Same message for wrong password and unknown email (no user enumeration).
- **500** – `error_code: "SYSTEM_ERROR"`.

---

#### `GET /api/v1/auth/profile`

Get current user profile. **Requires auth.**

**Headers:** `Authorization: Bearer <access_token>`

**Response (200):**

```json
{
  "status": "success",
  "data": {
    "id": "uuid-string",
    "email": "user@example.com",
    "full_name": "Jane Doe",
    "created_at": "2026-03-08T12:00:00.000000"
  },
  "message": "Profile retrieved successfully."
}
```

**Errors:**

- **401** – Missing token (`MISSING_TOKEN`), invalid token (`INVALID_TOKEN`), expired token (`TOKEN_EXPIRED`), or user not found (`USER_NOT_FOUND`).

---

### 6.3 Contacts (all require auth)

Send `Authorization: Bearer <access_token>` on every request.

#### `POST /api/v1/contacts`

Create a contact.

**Request body:**

| Field | Type | Required | Rules |
|-------|------|----------|--------|
| `name` | string | Yes | Min 1, max 255 |
| `relationship_type` | string | No | Max 100 |
| `birthday` | string | No | ISO date `YYYY-MM-DD` |

**Response (201):**

```json
{
  "status": "success",
  "data": {
    "id": "uuid-string",
    "name": "Alice",
    "relationship_type": "friend",
    "birthday": "1990-05-15",
    "created_at": "2026-03-08T12:00:00.000000",
    "memory_count": null
  },
  "message": "Contact added successfully"
}
```

**Errors:** 400 validation, 401 no/invalid token.

---

#### `GET /api/v1/contacts`

List all contacts for the current user.

**Response (200):**

```json
{
  "status": "success",
  "data": {
    "contacts": [
      {
        "id": "uuid-string",
        "name": "Alice",
        "relationship_type": "friend",
        "birthday": "1990-05-15",
        "created_at": "2026-03-08T12:00:00.000000",
        "memory_count": 3
      }
    ]
  },
  "message": ""
}
```

**Errors:** 401.

---

#### `GET /api/v1/contacts/{contact_id}`

Get one contact. `contact_id` is UUID.

**Response (200):** Same single-contact object as in the list (without `memory_count` required; may be present).

**Errors:**

- **401** – Not authenticated.
- **403** – Contact belongs to another user. `error_code: "FORBIDDEN"`.
- **404** – Contact not found. `error_code: "NOT_FOUND"`.
- **422/400** – Invalid UUID format; validation error.

---

#### `DELETE /api/v1/contacts/{contact_id}`

Delete a contact and its memories.

**Response (200):**

```json
{
  "status": "success",
  "data": null,
  "message": "Contact deleted successfully"
}
```

**Errors:** Same as GET contact (401, 403, 404, invalid UUID).

---

### 6.4 Memories (all require auth)

`contact_id` is UUID. User must own the contact.

#### `POST /api/v1/contacts/{contact_id}/memories`

Add a memory to a contact.

**Request body:**

| Field | Type | Required | Rules |
|-------|------|----------|--------|
| `content` | string | Yes | Min 1, max 5000 |

**Response (201):**

```json
{
  "status": "success",
  "data": {
    "id": "uuid-string",
    "content": "Loves dark chocolate",
    "created_at": "2026-03-08T12:00:00.000000"
  },
  "message": "Memory saved"
}
```

**Errors:** 400 validation, 401, 403 (not your contact), 404 (contact not found).

---

#### `GET /api/v1/contacts/{contact_id}/memories`

List memories for a contact (newest first).

**Response (200):**

```json
{
  "status": "success",
  "data": {
    "memories": [
      {
        "id": "uuid-string",
        "content": "Loves dark chocolate",
        "created_at": "2026-03-08T12:00:00.000000"
      }
    ]
  },
  "message": ""
}
```

**Errors:** 401, 403, 404 (same as above).

---

### 6.5 Calendar (requires auth)

#### `GET /api/v1/calendar`

List upcoming birthdays for the current user's contacts. Only contacts with a birthday set are included. Events are ordered by **next occurrence** (soonest first), so the calendar view can show "upcoming birthdays at a glance."

**Response (200):**

```json
{
  "status": "success",
  "data": {
    "events": [
      {
        "contact_id": "uuid-string",
        "contact_name": "Alice",
        "birthday": "1990-05-15",
        "next_occurrence": "2026-05-15",
        "days_until": 68
      }
    ]
  },
  "message": ""
}
```

| Field | Type | Description |
|-------|------|-------------|
| `contact_id` | string (UUID) | Link to the contact |
| `contact_name` | string | Display name |
| `birthday` | string | Original birthday, ISO date `YYYY-MM-DD` |
| `next_occurrence` | string | Next occurrence of the birthday (this year or next), ISO date |
| `days_until` | int | Days until `next_occurrence` (0 = today) |

**Notes:** Feb 29 birthdays in non-leap years use March 1 as the next occurrence. Empty list when the user has no contacts with a birthday set.

**Errors:** 401 (missing/invalid/expired token).

---

### Message for frontend: Calendar integration

**You can copy the block below and send it to the frontend team (Slack, email, or pin in your docs).**

---

**Calendar API is ready for integration**

The backend now exposes **`GET /api/v1/calendar`** so the Calendar page can show “upcoming birthdays at a glance” instead of “Coming Soon.”

**What you need to do**

1. **Call the endpoint** when the user opens the Calendar page (or when the app loads, if you prefetch).
   - **Method:** `GET`
   - **URL:** `${API_V1}/calendar` (e.g. `http://localhost:8000/api/v1/calendar`)
   - **Auth:** Send the same Bearer token as for contacts/memories: `Authorization: Bearer <access_token>`

2. **Handle the response** (same envelope as contacts/memories):
   - On success: `status === "success"`, use `data.events` (array of birthday events).
   - On 401: treat like other protected routes (e.g. clear token, redirect to login).

3. **Use each event** in `data.events`:
   - `contact_id` – use for linking to the contact (e.g. `/contacts/:id`).
   - `contact_name` – display name.
   - `birthday` – original birthday (ISO `YYYY-MM-DD`).
   - `next_occurrence` – next occurrence (this year or next), ISO date; use for “when” in the calendar.
   - `days_until` – number of days until that date (0 = today); use for “in X days” or sorting.

Events are **already ordered by next occurrence** (soonest first). If there are no contacts with a birthday, `data.events` is an empty array.

**Docs:** Full request/response shape and notes (e.g. Feb 29 → March 1 in non‑leap years) are in this guide under **6.5 Calendar**. Code example: **9.3 Fetch: get calendar (upcoming birthdays)**.

---

## 7. Error Handling

### 7.1 HTTP status codes

| Code | Meaning |
|------|--------|
| 200 | Success (GET, login/register, profile, list, delete) |
| 201 | Created (register, create contact, create memory) |
| 400 | Bad request (validation, malformed body) |
| 401 | Unauthorized (missing/invalid/expired token or wrong login) |
| 403 | Forbidden (valid token but no access to resource) |
| 404 | Not found (contact/resource does not exist or not owned) |
| 409 | Conflict (e.g. duplicate email) |
| 500 | Server error |

### 7.2 Error codes

Use these for branching in the UI (e.g. show “Session expired” for `TOKEN_EXPIRED`).

| `error_code` | HTTP | When |
|--------------|------|------|
| `VALIDATION_ERROR` | 400 | Invalid or missing request body/path params |
| `INVALID_CREDENTIALS` | 401 | Wrong email or password |
| `MISSING_TOKEN` | 401 | No `Authorization` header |
| `INVALID_TOKEN` | 401 | Malformed or invalid JWT |
| `TOKEN_EXPIRED` | 401 | JWT expired (24h) |
| `USER_NOT_FOUND` | 401 | User in token not in DB |
| `DUPLICATE_EMAIL` | 409 | Register with existing email |
| `FORBIDDEN` | 403 | Not owner of contact |
| `NOT_FOUND` | 404 | Resource not found |
| `SYSTEM_ERROR` | 500 | Internal error |

### 7.3 Validation errors

When `error_code === "VALIDATION_ERROR"`, use `details.field_errors` to show per-field messages. Shape:

```json
{
  "status": "error",
  "data": null,
  "message": "Request validation failed.",
  "error_code": "VALIDATION_ERROR",
  "details": {
    "field_errors": {
      "email": ["value is not a valid email address"],
      "password": ["ensure this value has at least 8 characters"]
    }
  }
}
```

Keys are field names (e.g. `email`, `password`, `body.content`); values are arrays of strings. Display the first message per field or join them.

### 7.4 Recommended client flow

1. Call API with correct headers and body.
2. Parse JSON (or handle non-JSON only for 5xx if needed).
3. If `response.status === "error"`:
   - Use `error_code` for generic handling (e.g. 401 → clear token, redirect to login).
   - Use `message` for toast/alert.
   - Use `details.field_errors` for inline form errors.
4. If `response.status === "success"`, use `data` (and optionally `message`).

---

## 8. Validation Rules (summary for frontend)

Use these for client-side validation to avoid unnecessary 400s:

| Endpoint | Field | Rules |
|----------|--------|--------|
| Register | `email` | Valid email |
| Register | `password` | Min 8 characters |
| Register | `full_name` | Optional, max 100 |
| Login | `email`, `password` | Required |
| Create contact | `name` | Required, 1–255 chars |
| Create contact | `relationship_type` | Optional, max 100 |
| Create contact | `birthday` | Optional, `YYYY-MM-DD` |
| Create memory | `content` | Required, 1–5000 chars |
| Path params | `contact_id` | Valid UUID |

---

## 9. Code Examples

### 9.1 Fetch: login and use token

```javascript
const API_V1 = 'http://localhost:8000/api/v1';

async function login(email, password) {
  const res = await fetch(`${API_V1}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  const json = await res.json();

  if (json.status === 'error') {
    throw new Error(json.message || 'Login failed');
  }

  const token = json.data.access_token;
  const user = json.data.user;
  return { token, user };
}

async function getProfile(token) {
  const res = await fetch(`${API_V1}/auth/profile`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const json = await res.json();

  if (json.status === 'error') {
    if (json.error_code === 'TOKEN_EXPIRED' || json.error_code === 'INVALID_TOKEN') {
      // Clear token and redirect to login
    }
    throw new Error(json.message);
  }

  return json.data;
}
```

### 9.2 Fetch: create contact

```javascript
async function createContact(token, { name, relationship_type, birthday }) {
  const res = await fetch(`${API_V1}/contacts`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ name, relationship_type, birthday }),
  });
  const json = await res.json();

  if (json.status === 'error') {
    if (json.error_code === 'VALIDATION_ERROR' && json.details?.field_errors) {
      return { ok: false, fieldErrors: json.details.field_errors };
    }
    throw new Error(json.message);
  }

  return { ok: true, contact: json.data };
}
```

### 9.3 Fetch: get calendar (upcoming birthdays)

```javascript
async function getCalendarEvents(token) {
  const res = await fetch(`${API_V1}/calendar`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const json = await res.json();

  if (json.status === 'error') {
    if (json.error_code === 'TOKEN_EXPIRED' || json.error_code === 'INVALID_TOKEN') {
      // Clear token and redirect to login
    }
    throw new Error(json.message);
  }

  // data.events is already sorted by next_occurrence (soonest first)
  return json.data.events;
}

// Usage: replace "Coming Soon" on /calendar with this data
// const events = await getCalendarEvents(accessToken);
// events.forEach((e) => {
//   e.contact_id, e.contact_name, e.birthday, e.next_occurrence, e.days_until
// });
```

### 9.4 Axios: shared client with interceptors

```javascript
import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const api = axios.create({
  baseURL: `${API_BASE}/api/v1`,
  headers: { 'Content-Type': 'application/json' },
});

// Add token to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Handle envelope and 401
api.interceptors.response.use(
  (response) => {
    const body = response.data;
    if (body.status === 'error') {
      return Promise.reject({ response, data: body });
    }
    return response;
  },
  (error) => {
    const data = error.response?.data;
    if (data?.status === 'error' && [401].includes(error.response?.status)) {
      if (['TOKEN_EXPIRED', 'INVALID_TOKEN', 'MISSING_TOKEN'].includes(data.error_code)) {
        localStorage.removeItem('access_token');
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

// Usage
await api.post('/auth/login', { email, password });
const { data } = await api.get('/contacts');
const contacts = data.data.contacts;

// Calendar (upcoming birthdays, already sorted by next_occurrence)
const cal = await api.get('/calendar');
const events = cal.data.data.events; // [{ contact_id, contact_name, birthday, next_occurrence, days_until }, ...]
```

---

## 10. Integration Checklist

Use this to verify integration in one shot:

- [ ] **Environment:** Base URL in env var; all requests go to `{base}/api/v1/...`.
- [ ] **Headers:** `Content-Type: application/json` for POST/PUT; `Authorization: Bearer <token>` for protected routes.
- [ ] **Envelope:** Every response parsed as JSON; check `status === "success"` or `"error"`; use `data` or `message`/`error_code`/`details`.
- [ ] **Auth:** Register and login store `access_token` and send it on contacts and memories.
- [ ] **401:** On `TOKEN_EXPIRED` / `INVALID_TOKEN` / `MISSING_TOKEN`, clear token and redirect to login.
- [ ] **Validation:** On `VALIDATION_ERROR`, read `details.field_errors` and show per-field errors.
- [ ] **CORS:** Frontend origin is `http://localhost:8080` or `http://127.0.0.1:8080`, or backend has your origin in `allow_origins`.
- [ ] **Contacts:** Create (POST), list (GET), get one (GET by id), delete (DELETE); handle 403/404.
- [ ] **Memories:** Create (POST `/{contact_id}/memories`), list (GET `/{contact_id}/memories`); handle 403/404 for wrong contact.
- [ ] **Calendar:** List upcoming birthdays (GET `/calendar`); use `data.events` (contact_id, contact_name, birthday, next_occurrence, days_until); 401 when not authenticated.
- [ ] **IDs:** All IDs (user, contact, memory) are UUIDs; use them as strings in path and request/response.
- [ ] **Dates:** All date/time fields are ISO 8601 strings (e.g. `created_at`).

---

## References

- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`
- **API testing report:** `docs/API_TESTING_FINDINGS.md`
- **Backend structure:** `docs/backend_structure.md`

If something doesn’t match this guide, confirm the backend version and that you’re using the same base URL and `/api/v1` prefix. For new environments (e.g. staging), ensure CORS and base URL are updated.
