"""
Main FastAPI application
"""

from contextlib import asynccontextmanager
from datetime import date
import json
import logging
import uuid
from urllib import request as urlrequest
from urllib.error import URLError

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from app.core.config import settings
from app.database import create_db_and_tables, engine, get_session
from app.models import Contact, Memory, User

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DEV_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


class ContactCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    relationship_type: str | None = None
    birthday: date | None = None


class ContactUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    relationship_type: str | None = None
    birthday: date | None = None


class MemoryCreate(BaseModel):
    content: str = Field(min_length=1)


def ok(data):
    return {"status": "success", "data": data}


def contact_data(session: Session, contact: Contact):
    memory_count = len(session.exec(select(Memory).where(Memory.contact_id == contact.id)).all())
    return {
        "id": str(contact.id),
        "name": contact.name,
        "relationship_type": contact.relationship_type,
        "birthday": contact.birthday.isoformat() if contact.birthday else None,
        "created_at": contact.created_at.isoformat(),
        "memory_count": memory_count,
    }


def memory_data(memory: Memory):
    return {
        "id": str(memory.id),
        "content": memory.content,
        "created_at": memory.created_at.isoformat(),
    }


def user_data(user: User):
    return {
        "id": str(user.id),
        "email": user.email,
        "created_at": user.created_at.isoformat(),
    }


def ai_status():
    configured = bool(settings.OPENROUTER_API_KEY)
    return {
        "provider": "openrouter" if configured else "local_fallback",
        "model": settings.OPENROUTER_MODEL if configured else "local rules",
        "configured": configured,
    }


def ensure_dev_user(session: Session):
    user = session.get(User, DEV_USER_ID)
    if not user:
        session.add(User(id=DEV_USER_ID, email="dev@giftgenius.local", password_hash="dev"))
        session.commit()


def fallback_recommendations(contact: Contact, memories: list[Memory]):
    hints = " ".join(memory.content.lower() for memory in memories)
    ideas = [
        f"A thoughtful card plus something tied to {contact.relationship_type or 'your relationship'}",
        "A shared-experience gift like dinner, an event, or a workshop",
        "A small premium everyday item they would use often",
    ]
    if "coffee" in hints:
        ideas.insert(0, "Specialty coffee beans or a cafe gift card")
    if "book" in hints or "read" in hints:
        ideas.insert(0, "A book in their favorite genre with a handwritten note")
    if "fitness" in hints or "gym" in hints:
        ideas.insert(0, "A useful fitness accessory or recovery tool")
    return ideas[:5]


def parse_ai_ideas(content: str) -> list[str] | None:
    content = content.strip()
    if content.startswith("```"):
        content = content.strip("`")
        content = content.removeprefix("json").strip()
    if not content.startswith("["):
        start = content.find("[")
        end = content.rfind("]")
        if start != -1 and end != -1:
            content = content[start:end + 1]
    parsed = json.loads(content)
    if not isinstance(parsed, list):
        return None
    ideas = [str(item).strip() for item in parsed if str(item).strip()]
    return ideas[:5] or None


def ai_recommendations(contact: Contact, memories: list[Memory]):
    if not settings.OPENROUTER_API_KEY:
        return fallback_recommendations(contact, memories)

    prompt = (
        "Suggest 5 concise gift ideas. Return only a JSON array of strings.\n"
        f"Contact: {contact.name}\n"
        f"Relationship: {contact.relationship_type or 'Unknown'}\n"
        f"Birthday: {contact.birthday or 'Unknown'}\n"
        f"Notes: {[memory.content for memory in memories]}"
    )
    body = json.dumps({
        "model": settings.OPENROUTER_MODEL,
        "messages": [{"role": "user", "content": prompt}],
    }).encode("utf-8")
    req = urlrequest.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=body,
        headers={
            "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:8080",
            "X-Title": "GiftGenius",
        },
        method="POST",
    )
    try:
        with urlrequest.urlopen(req, timeout=20) as response:
            content = json.loads(response.read().decode("utf-8"))["choices"][0]["message"]["content"]
        return parse_ai_ideas(content) or fallback_recommendations(contact, memories)
    except (KeyError, json.JSONDecodeError, TimeoutError, URLError) as exc:
        logger.warning("AI recommendations fell back: %s", exc)
        return fallback_recommendations(contact, memories)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    logger.info("🚀 Starting GiftGenius API...")
    create_db_and_tables()
    with Session(engine) as session:
        ensure_dev_user(session)
    logger.info("✅ Application startup complete")
    
    yield
    
    # Shutdown
    logger.info("👋 Shutting down GiftGenius API...")


app = FastAPI(
    title="GiftGenius API",
    version="1.0.0",
    description="AI-powered gift recommendation system",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://127.0.0.1:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    """Health check endpoint"""
    return {
        "status": "success",
        "data": {
            "message": "GiftGenius API is running",
            "version": "1.0.0",
            "environment": settings.ENVIRONMENT
        }
    }


@app.get("/health")
def health_check():
    """Detailed health check"""
    try:
        with Session(engine) as session:
            session.exec(select(User).limit(1)).first()
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    return {
        "status": "success",
        "data": {
            "api": "healthy",
            "database": db_status,
            "environment": settings.ENVIRONMENT
        }
    }


@app.get("/api/v1/contacts")
def list_contacts(session: Session = Depends(get_session)):
    contacts = session.exec(select(Contact).order_by(Contact.created_at.desc())).all()
    return ok({"contacts": [contact_data(session, contact) for contact in contacts]})


@app.get("/api/v1/dev/db-snapshot")
def dev_db_snapshot(session: Session = Depends(get_session)):
    if settings.ENVIRONMENT == "production":
        raise HTTPException(status_code=404, detail="Not found")
    users = session.exec(select(User).order_by(User.created_at.desc()).limit(5)).all()
    contacts = session.exec(select(Contact).order_by(Contact.created_at.desc()).limit(10)).all()
    memories = session.exec(select(Memory).order_by(Memory.created_at.desc()).limit(10)).all()
    return ok({
        "database_url": "sqlite" if settings.DATABASE_URL.startswith("sqlite") else "postgres",
        "counts": {
            "users": len(session.exec(select(User)).all()),
            "contacts": len(session.exec(select(Contact)).all()),
            "memories": len(session.exec(select(Memory)).all()),
        },
        "ai": ai_status(),
        "users": [user_data(user) for user in users],
        "contacts": [contact_data(session, contact) for contact in contacts],
        "memories": [memory_data(memory) for memory in memories],
    })


@app.post("/api/v1/contacts", status_code=201)
def create_contact(payload: ContactCreate, session: Session = Depends(get_session)):
    ensure_dev_user(session)
    contact = Contact(
        name=payload.name.strip(),
        relationship_type=payload.relationship_type,
        birthday=payload.birthday,
        user_id=DEV_USER_ID,
    )
    session.add(contact)
    session.commit()
    session.refresh(contact)
    return ok(contact_data(session, contact))


@app.put("/api/v1/contacts/{contact_id}")
def update_contact(contact_id: uuid.UUID, payload: ContactUpdate, session: Session = Depends(get_session)):
    contact = session.get(Contact, contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    if payload.name is not None:
        contact.name = payload.name.strip()
    if payload.relationship_type is not None:
        contact.relationship_type = payload.relationship_type
    if payload.birthday is not None:
        contact.birthday = payload.birthday
    session.add(contact)
    session.commit()
    session.refresh(contact)
    return ok(contact_data(session, contact))


@app.delete("/api/v1/contacts/{contact_id}")
def delete_contact(contact_id: uuid.UUID, session: Session = Depends(get_session)):
    contact = session.get(Contact, contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    for memory in session.exec(select(Memory).where(Memory.contact_id == contact_id)).all():
        session.delete(memory)
    session.delete(contact)
    session.commit()
    return ok(None)


@app.get("/api/v1/contacts/{contact_id}/memories")
def list_memories(contact_id: uuid.UUID, session: Session = Depends(get_session)):
    if not session.get(Contact, contact_id):
        raise HTTPException(status_code=404, detail="Contact not found")
    memories = session.exec(select(Memory).where(Memory.contact_id == contact_id).order_by(Memory.created_at.desc())).all()
    return ok({"memories": [memory_data(memory) for memory in memories]})


@app.post("/api/v1/contacts/{contact_id}/memories", status_code=201)
def create_memory(contact_id: uuid.UUID, payload: MemoryCreate, session: Session = Depends(get_session)):
    if not session.get(Contact, contact_id):
        raise HTTPException(status_code=404, detail="Contact not found")
    memory = Memory(content=payload.content.strip(), contact_id=contact_id)
    session.add(memory)
    session.commit()
    session.refresh(memory)
    return ok(memory_data(memory))


@app.delete("/api/v1/contacts/{contact_id}/memories/{memory_id}")
def delete_memory(contact_id: uuid.UUID, memory_id: uuid.UUID, session: Session = Depends(get_session)):
    memory = session.get(Memory, memory_id)
    if not memory or memory.contact_id != contact_id:
        raise HTTPException(status_code=404, detail="Memory not found")
    session.delete(memory)
    session.commit()
    return ok(None)


@app.get("/api/v1/contacts/{contact_id}/recommendations")
def recommend_gifts(contact_id: uuid.UUID, session: Session = Depends(get_session)):
    contact = session.get(Contact, contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    memories = session.exec(select(Memory).where(Memory.contact_id == contact_id)).all()
    return ok({"recommendations": ai_recommendations(contact, memories)})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
