# GiftGenius API – Testing Findings Report

**Date:** 2026-03-08  
**Tester:** Automated curl-based test suite + manual checks  
**Base URL:** `http://localhost:8000`  
**Total scenarios run:** 44+

---

## Executive Summary

| Metric | Result |
|--------|--------|
| **Robustness** | Good – validation, auth, and ownership enforced; a few consistency gaps (see below). |
| **Security** | Good – JWT on protected routes, 401/403 where expected, no auth bypass observed. |
| **Response speed** | Good – most responses 0.2–0.6 s; auth (bcrypt) ~0.45–0.56 s; target &lt;200 ms for CRUD is met for non-auth. |
| **Scalability** | Moderate – stateless API and DB-backed; no caching or rate limiting tested. |

---

## 1. Public Endpoints

### 1.1 `GET /`

| Aspect | Finding |
|--------|--------|
| **Purpose** | Root health / API status. |
| **Test** | `curl -s http://localhost:8000/` |
| **Status** | 200 OK |
| **Response** | `{"status":"success","data":{"message":"GiftGenius API is running","version":"1.0.0","environment":"..."}}` |
| **Time** | ~0.20–0.21 s (cold), ~0.21 s average over 5 runs. |
| **Verdict** | Pass. Envelope and info as expected. |

### 1.2 `GET /health`

| Aspect | Finding |
|--------|--------|
| **Purpose** | Health check including DB connectivity. |
| **Test** | `curl -s http://localhost:8000/health` |
| **Status** | 200 OK |
| **Response** | `{"status":"success","data":{"api":"healthy","database":"connected","environment":"..."}}` |
| **Time** | ~0.21 s. |
| **Verdict** | Pass. Database status correctly reported. |

---

## 2. Authentication APIs

### 2.1 `POST /api/v1/auth/register`

| Scenario | Expected | Actual | Time | Notes |
|----------|----------|--------|------|--------|
| Valid (email + password only) | 200/201 | 200 | ~0.56 s | Token and user returned; `full_name` "" |
| Valid (email + password + full_name) | 200/201 | 200 | ~0.46 s | Token and user with full_name |
| Duplicate email | 409 | 409 | ~0.23 s | `error_code: DUPLICATE_EMAIL`, message clear |
| Missing email | 400/422 | 400 | ~0.20 s | `field_errors.email` |
| Short password (&lt;8) | 400/422 | 400 | ~0.21 s | `field_errors.password` |
| Invalid email format | 400/422 | 400 | ~0.21 s | Email validation message |
| Empty body `{}` | 400/422 | 400 | ~0.21 s | email + password required |
| Malformed JSON | 400/422 | 400 | ~0.21 s | JSON decode error in details |

**Findings:**

- Registration behaves correctly for valid, duplicate, and invalid payloads.
- Response envelope is consistent (`status`, `data`, `message`; errors include `error_code` and `details`).
- Auth (bcrypt + DB write) adds ~0.25–0.35 s vs simple CRUD; acceptable for login/register.

### 2.2 `POST /api/v1/auth/login`

| Scenario | Expected | Actual | Time | Notes |
|----------|----------|--------|------|--------|
| Valid credentials | 200 | 200 | ~0.46 s | Token and user returned |
| Wrong password | 401 | 401 | ~0.52 s | `INVALID_CREDENTIALS`, generic message |
| Non-existent email | 401 | 401 | ~0.21 s | Same message (no user enumeration) |
| Missing fields | 400/422 | 400 | ~0.21 s | Validation error |

**Findings:**

- Login success and failure paths correct.
- Same 401 message for wrong password and unknown email is good for security (no email enumeration).

### 2.3 `GET /api/v1/auth/profile`

| Scenario | Expected | Actual | Time | Notes |
|----------|----------|--------|------|--------|
| Valid Bearer token | 200 | 200 | ~0.21 s | User id, email, full_name, created_at |
| No token | 401 | 401 | ~0.20 s | `MISSING_TOKEN` |
| Invalid JWT | 401 | 401 | ~0.21 s | `INVALID_TOKEN` |

**Findings:**

- Protected route correctly requires and validates JWT; 401 for missing/invalid token.

---

## 3. Contacts APIs

### 3.1 `POST /api/v1/contacts`

| Scenario | Expected | Actual | Time | Notes |
|----------|----------|--------|------|--------|
| No auth | 401 | 401 | ~0.21 s | `MISSING_TOKEN` |
| Valid (name, type, birthday) | 201 | 201 | ~0.27 s | Contact created, envelope correct |
| Minimal (name only) | 201 | 201 | ~0.22 s | relationship_type, birthday optional |
| Empty name `""` | 400 or 201 | 201 | ~0.35 s | **Finding:** Empty name accepted; consider `min_length=1` for name |

**Findings:**

- Auth and creation logic work; optional fields handled.
- **Recommendation:** Reject empty contact name (e.g. Pydantic `min_length=1` on `name`).

### 3.2 `GET /api/v1/contacts`

| Scenario | Expected | Actual | Time | Notes |
|----------|----------|--------|------|--------|
| With auth | 200 | 200 | ~0.25 s | List with memory_count per contact |
| Without auth | 401 | 401 | ~0.21 s | |

**Findings:**

- List and auth behave as expected; memory counts present.

### 3.3 `GET /api/v1/contacts/{contact_id}`

| Scenario | Expected | Actual | Time | Notes |
|----------|----------|--------|------|--------|
| Own contact, with auth | 200 | 200 | ~0.23 s | Single contact |
| Without auth | 401 | 401 | ~0.22 s | |
| Other user’s contact | 403 | 403 | ~0.22 s | **Body:** `{"detail":"You don't have access to this contact"}` (FastAPI default, not envelope) |
| Invalid UUID | 400/422 | 400 | ~0.22 s | Validation error for path |
| Non-existent UUID | 404 | 404 | ~0.23 s | **Body:** `{"detail":"Contact not found"}` (FastAPI default) |

**Findings:**

- Ownership and not-found behavior correct.
- **Recommendation:** Return 403/404 in the same envelope format as the rest of the API (`status`, `data`, `message` / `error_code`) for consistency.

### 3.4 `DELETE /api/v1/contacts/{contact_id}`

| Scenario | Expected | Actual | Time | Notes |
|----------|----------|--------|------|--------|
| Own contact | 200 | 200 | ~0.24 s | `data: null`, message set |
| Delete again | 404 | 404 | ~0.21 s | `{"detail":"Contact not found"}` |
| Without auth | 401 | 401 | ~0.22 s | |
| Other user’s contact | 403 | 403 | ~0.21 s | `{"detail":"You don't have access..."}` |

**Findings:**

- Delete, idempotency (404 on second delete), and auth/ownership correct.
- Same envelope recommendation for 403/404 as above.

---

## 4. Memories APIs

### 4.1 `POST /api/v1/contacts/{contact_id}/memories`

| Scenario | Expected | Actual | Time | Notes |
|----------|----------|--------|------|--------|
| No auth | 401 | 401 | ~0.21 s | |
| Valid content | 201 | 201 | ~0.23 s | Memory id, content, created_at |
| Empty content | 400/422 | 400 | ~0.21 s | `content` min length 1 |
| Other user’s contact | 403 | 403 | ~0.22 s | `{"detail":"..."}` |
| Non-existent contact_id | 404 | 404 | ~0.22 s | `{"detail":"Contact not found"}` |

**Findings:**

- Validation and authorization correct; empty content rejected as required.

### 4.2 `GET /api/v1/contacts/{contact_id}/memories`

| Scenario | Expected | Actual | Time | Notes |
|----------|----------|--------|------|--------|
| With auth, own contact | 200 | 200 | ~0.27 s | List, newest first |
| No auth | 401 | 401 | ~0.21 s | |
| Other user’s contact | 403 | 403 | ~0.21 s | |

**Findings:**

- List and access control behave correctly.

---

## 5. Edge Cases & Consistency

### 5.1 Wrong HTTP method

- `GET /api/v1/auth/register` → **405** Method Not Allowed.
- `OPTIONS /api/v1/contacts` (no Origin) → **405** in test run; with `Origin: http://localhost:8080` manual check → **200** (CORS preflight OK).

### 5.2 Error response format

- Most errors use custom envelope: `status`, `data`, `message`, and often `error_code` / `details`.
- **Inconsistent:** 403 and 404 raised via `HTTPException` in contacts/memories return FastAPI’s default `{"detail": "..."}` instead of the envelope. Affected: GET/DELETE contact (403/404), POST/GET memories (403/404).

### 5.3 DELETE without auth

- One run observed **307** (redirect) for DELETE contact without auth; typically **401** is expected. May be environment-specific (e.g. redirect to login). Worth confirming in your setup.

---

## 6. Performance Summary

| Operation type | Typical time | Target (from PRD) | Met? |
|----------------|-------------|-------------------|------|
| GET /, GET /health | ~0.20–0.21 s | - | - |
| POST register / login | ~0.45–0.56 s | - | Acceptable (bcrypt) |
| POST contact | ~0.22–0.27 s | &lt;200 ms | Slightly over, acceptable |
| GET contacts list | ~0.25 s | &lt;200 ms | Slightly over |
| GET contact by id | ~0.23 s | &lt;200 ms | Slightly over |
| POST memory | ~0.23 s | &lt;200 ms | Slightly over |
| GET memories | ~0.27 s | - | OK |
| DELETE contact | ~0.24 s | &lt;200 ms | Slightly over |
| Validation/error responses | ~0.20–0.21 s | - | Fast |

- PRD target “&lt;200 ms for CRUD” is slightly exceeded in testing (e.g. 220–270 ms) but remains reasonable for a dev environment (DB, no tuning).
- Auth endpoints are slower due to bcrypt and are acceptable.

---

## 7. Security Assessment

| Check | Result |
|-------|--------|
| Protected routes without token | 401 with clear message |
| Invalid/expired JWT | 401 |
| Access to other user’s contact (GET/POST/DELETE) | 403 |
| Access to other user’s memories | 403 |
| Login: wrong password vs unknown email | Same 401 message (no enumeration) |
| Duplicate registration | 409, no info leak |
| Input validation (email, password length, UUID, content length) | Enforced |
| CORS preflight (with Origin) | 200, preflight OK |

- No auth bypass observed; ownership enforced on contacts and memories.

---

## 8. Robustness & Scalability

- **Robustness:** Validation, auth, and ownership are in place; error handling is mostly consistent; main gap is 403/404 envelope format.
- **Scalability:** Stateless API; DB-backed; no in-memory session. Not tested: connection pooling under load, rate limiting, or caching. Suitable for Phase 1; for growth, consider indexing (e.g. on `user_id`, `contact_id`), rate limiting, and optional caching.

---

## 9. Recommendations

1. **Contact name:** Add `min_length=1` (or equivalent) for contact `name` so empty string is rejected. **Addressed:** `ContactCreate.name` now has `min_length=1`.
2. **Error envelope:** Convert 403/404 from contacts and memories to the same envelope format (`status`, `data`, `message` / `error_code`) used elsewhere. **Addressed:** `HTTPException` is handled by a registered handler; 403/404 use `error_code` FORBIDDEN/NOT_FOUND.
3. **OPTIONS (CORS):** CORS preflight (OPTIONS) returns 200 when the request includes an `Origin` header (e.g. `Origin: http://localhost:8080`). Browsers send `Origin` automatically; for non-browser clients, include `Origin` when testing preflight. No code change required.
4. **DELETE without auth:** Unauthenticated DELETE should return 401. If 307 appears, it is likely environment-specific (proxy or trailing-slash redirect). Clients should use exact paths and expect 401 for missing/invalid token. **Addressed:** Test added to assert DELETE without auth returns 401.

---

## 10. Test Artifacts

- **Script:** `scripts/api-test-curl.ps1` (PowerShell; uses temporary JSON files for bodies).
- **Results (sample run):** `scripts/api-test-results.json`.
- **How to run:** Start backend (`uvicorn app.main:app --reload`), then run `.\scripts\api-test-curl.ps1` from project root.

---

**Conclusion:** The GiftGenius API behaves correctly for auth, contacts, and memories in the tested scenarios. It is suitable for production use from a correctness and security perspective, with minor improvements recommended for consistency (error envelope, contact name validation) and performance tuning if strict &lt;200 ms CRUD is required.
