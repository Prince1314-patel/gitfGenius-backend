"""
Memory management endpoints.

Provides create and list operations for memories linked to a contact.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.database import get_session
from app.models import Contact, Memory, User
from app.schemas import (
    MemoryCreate,
    MemoryResponse,
    MemoryListData,
    StandardResponse,
)
from app.core.security import get_current_user

router = APIRouter(prefix="/contacts", tags=["memories"])


def _get_contact_or_raise(
    contact_id: uuid.UUID,
    current_user: User,
    db: Session,
) -> Contact:
    """Get contact by id; raise 404 if not found, 403 if not owned by user."""
    contact = db.get(Contact, contact_id)
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found",
        )
    if contact.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this contact",
        )
    return contact


@router.post(
    "/{contact_id}/memories",
    response_model=StandardResponse[MemoryResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_memory(
    contact_id: uuid.UUID,
    memory_data: MemoryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
) -> StandardResponse[MemoryResponse]:
    """Add a memory to a contact. Returns 404 if contact not found, 403 if not owned by user."""
    _get_contact_or_raise(contact_id, current_user, db)
    new_memory = Memory(content=memory_data.content, contact_id=contact_id)
    db.add(new_memory)
    db.commit()
    db.refresh(new_memory)
    return StandardResponse[MemoryResponse](
        status="success",
        data=MemoryResponse(
            id=str(new_memory.id),
            content=new_memory.content,
            created_at=new_memory.created_at.isoformat(),
        ),
        message="Memory saved",
    )


@router.get(
    "/{contact_id}/memories",
    response_model=StandardResponse[MemoryListData],
)
async def list_memories(
    contact_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
) -> StandardResponse[MemoryListData]:
    """List all memories for a contact (newest first). Returns 404 if contact not found, 403 if not owned."""
    _get_contact_or_raise(contact_id, current_user, db)
    memories = db.exec(
        select(Memory)
        .where(Memory.contact_id == contact_id)
        .order_by(Memory.created_at.desc())
    ).all()
    memories_data = [
        MemoryResponse(
            id=str(m.id),
            content=m.content,
            created_at=m.created_at.isoformat(),
        )
        for m in memories
    ]
    return StandardResponse[MemoryListData](
        status="success",
        data=MemoryListData(memories=memories_data),
        message="",
    )
