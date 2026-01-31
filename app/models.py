from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List
import uuid

from sqlmodel import SQLModel, Field, Relationship


class RelationshipType(str, Enum):
    FRIEND = "Friend"
    FAMILY = "Family"
    COLLEAGUE = "Colleague"
    PARTNER = "Partner"
    OTHER = "Other"


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    email: str = Field(unique=True, index=True, max_length=255)
    password_hash: str = Field(max_length=255)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Relationships
    contacts: List["Contact"] = Relationship(back_populates="user", cascade_delete=True)


class Contact(SQLModel, table=True):
    __tablename__ = "contacts"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(max_length=100)
    relationship_type: RelationshipType = Field(default=RelationshipType.FRIEND)
    birthday: Optional[datetime] = Field(default=None)  # Using datetime for date to simplify, or date
    user_id: uuid.UUID = Field(foreign_key="users.id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Relationships
    user: User = Relationship(back_populates="contacts")
    memories: List["Memory"] = Relationship(back_populates="contact", cascade_delete=True)


class Memory(SQLModel, table=True):
    __tablename__ = "memories"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    content: str = Field(max_length=5000)
    contact_id: uuid.UUID = Field(foreign_key="contacts.id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Relationships
    contact: Contact = Relationship(back_populates="memories")
