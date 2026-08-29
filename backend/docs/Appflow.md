# Product Requirements Document (PRD)
## GiftGenius - Phase 1 (Walking Skeleton)

### Product Overview
**Product Name:** GiftGenius  
**Version:** Phase 1 - Walking Skeleton (MVP Infrastructure)  
**Last Updated:** January 26, 2026

### Vision Statement
GiftGenius is a relationship management system that captures unstructured memories about friends and loved ones to later generate personalized gift ideas.

### Problem Statement
Users struggle to remember small details about their friends' preferences, interests, and casual mentions throughout the year. This leads to:
- Generic, thoughtless gifts
- Last-minute gift panic
- Missed opportunities to show thoughtfulness
- Forgetting important life events and preferences

### Solution
A "Second Brain" for relationships that:
- Stores contacts with basic information
- Captures casual memories and observations
- Creates a searchable knowledge base per person
- (Future) Generates AI-powered gift suggestions

---

## Phase 1 Scope: Walking Skeleton

### In Scope ✅

**1. User Authentication**
- User registration with email and password
- Secure login with JWT token generation
- Password hashing with Bcrypt
- Token-based session management

**2. Contact Management**
- Create new contacts with name, relationship type, and birthday
- View all contacts in a dashboard
- View individual contact details
- Delete contacts
- Each contact linked to authenticated user

**3. Memory Logging**
- Add text-based memories/notes for specific contacts
- View all memories for a contact in chronological order
- Simple text input (no rich text in Phase 1)
- Memories automatically timestamped

**4. Data Persistence**
- PostgreSQL database for all data
- Docker containerization for easy deployment
- Data survives container restarts
- Relational integrity (User → Contacts → Memories)

---

## Out of Scope ❌ (Future Phases)

- ❌ AI-powered gift generation (LangGraph integration)
- ❌ Gift suggestions or recommendations
- ❌ Reminders and notifications
- ❌ Image uploads or attachments
- ❌ Rich text formatting in memories
- ❌ Social features or sharing
- ❌ Mobile apps
- ❌ Email notifications
- ❌ Calendar integrations
- ❌ Search functionality
- ❌ Tags or categories

---

## Success Criteria

**Phase 1 is considered successful when:**

1. ✅ A user can register and login successfully
2. ✅ A user can create at least 3 contacts
3. ✅ A user can add at least 5 memories to a contact
4. ✅ Data persists after Docker restart
5. ✅ Frontend and Backend communicate seamlessly
6. ✅ No authentication bypass vulnerabilities
7. ✅ All API endpoints return proper response formats

---

## User Stories

### Epic 1: Authentication
**US-1.1:** As a new user, I want to register with email and password so that I can access the system  
**US-1.2:** As a registered user, I want to login securely so that I can access my data  
**US-1.3:** As a logged-in user, I want my session to persist so that I don't have to login repeatedly

### Epic 2: Contact Management
**US-2.1:** As a user, I want to add a new contact with name, relationship, and birthday  
**US-2.2:** As a user, I want to see all my contacts on a dashboard  
**US-2.3:** As a user, I want to view a specific contact's profile  
**US-2.4:** As a user, I want to delete a contact I no longer need

### Epic 3: Memory Capture
**US-3.1:** As a user, I want to add a memory/note about a contact  
**US-3.2:** As a user, I want to see all memories for a contact in order  
**US-3.3:** As a user, I want memories to be timestamped automatically

---

## Data Model (Simplified)

```
User
├── id (UUID)
├── email (unique)
├── password_hash
└── created_at

Contact
├── id (UUID)
├── user_id (FK → User)
├── name
├── relationship_type
├── birthday
└── created_at

Memory
├── id (UUID)
├── contact_id (FK → Contact)
├── content (text)
└── created_at
```

---

## Technical Constraints

- Backend must be in Python (FastAPI)
- Database must be PostgreSQL
- Must run in Docker containers
- Frontend is already built (React + Vite)
- JWT tokens must expire in 24 hours
- All passwords must be hashed with Bcrypt

---

## Non-Functional Requirements

**Performance:**
- API response time < 200ms for CRUD operations
- Support up to 100 contacts per user
- Support up to 1000 memories per contact

**Security:**
- Passwords must be hashed (never stored plain text)
- JWT tokens for authentication
- CORS properly configured
- SQL injection protection via ORM

**Usability:**
- API must return clear error messages
- Response format must be consistent
- Swagger UI documentation available

---

## Assumptions

1. Users have stable internet connection
2. Users access via desktop/laptop browsers
3. Single user per account (no sharing)
4. English language only in Phase 1
5. Users manage < 50 contacts typically

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Frontend-Backend mismatch | High | Strict API contract documentation |
| Data loss on restart | High | Docker volumes for Postgres |
| Authentication bypass | Critical | JWT validation on every protected route |
| Slow database queries | Medium | Proper indexing on foreign keys |

---

## Future Roadmap (Post Phase 1)

**Phase 2:** AI Integration
- LangGraph for gift generation
- Vector embeddings for semantic search

**Phase 3:** Enhanced UX
- Image uploads
- Rich text memories
- Tags and categories

**Phase 4:** Notifications
- Birthday reminders
- Gift deadline alerts

---

## Approval & Sign-off

**Approved By:** [Your Name]  
**Date:** January 26, 2026  
**Status:** ✅ Ready for Development