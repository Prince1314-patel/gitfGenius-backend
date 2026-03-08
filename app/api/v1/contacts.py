"""
Contact management endpoints.

Provides CRUD operations for contacts linked to the authenticated user.
"""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select, func

from app.database import get_session
from app.models import Contact, Memory, User
from app.schemas import (
    ContactCreate,
    ContactResponse,
    ContactListData,
    StandardResponse,
)
from app.core.security import get_current_user

router = APIRouter(prefix="/contacts", tags=["contacts"])


def _contact_to_response(contact: Contact, memory_count: Optional[int] = None) -> ContactResponse:
    """Build ContactResponse from Contact model."""
    return ContactResponse(
        id=str(contact.id),
        name=contact.name,
        relationship_type=contact.relationship_type,
        birthday=contact.birthday.isoformat() if contact.birthday else None,
        created_at=contact.created_at.isoformat(),
        memory_count=memory_count,
    )


@router.post("", response_model=StandardResponse[ContactResponse], status_code=status.HTTP_201_CREATED)
async def create_contact(
    contact_data: ContactCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
) -> StandardResponse[ContactResponse]:
    """Create a new contact for the authenticated user."""
    new_contact = Contact(
        **contact_data.model_dump(),
        user_id=current_user.id,
    )
    db.add(new_contact)
    db.commit()
    db.refresh(new_contact)
    return StandardResponse[ContactResponse](
        status="success",
        data=_contact_to_response(new_contact),
        message="Contact added successfully",
    )


@router.get("", response_model=StandardResponse[ContactListData])
async def list_contacts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
) -> StandardResponse[ContactListData]:
    """List all contacts for the authenticated user with memory counts."""
    contacts = db.exec(select(Contact).where(Contact.user_id == current_user.id)).all()
    contacts_data = []
    for contact in contacts:
        count_result = db.exec(
            select(func.count(Memory.id)).where(Memory.contact_id == contact.id)
        ).one()
        contacts_data.append(_contact_to_response(contact, memory_count=count_result))
    return StandardResponse[ContactListData](
        status="success",
        data=ContactListData(contacts=contacts_data),
        message="",
    )


@router.get("/{contact_id}", response_model=StandardResponse[ContactResponse])
async def get_contact(
    contact_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
) -> StandardResponse[ContactResponse]:
    """Get a single contact by id. Returns 404 if not found, 403 if not owned by user."""
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
    return StandardResponse[ContactResponse](
        status="success",
        data=_contact_to_response(contact),
        message="",
    )


@router.delete("/{contact_id}", response_model=StandardResponse[None])
async def delete_contact(
    contact_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
) -> StandardResponse[None]:
    """Delete a contact and its memories. Returns 404 if not found, 403 if not owned by user."""
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
    db.delete(contact)
    db.commit()
    return StandardResponse[None](
        status="success",
        data=None,
        message="Contact deleted successfully",
    )
