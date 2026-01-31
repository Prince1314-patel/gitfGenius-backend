"""
Database models definition using SQLModel.
"""

from typing import Optional
from datetime import date, datetime
import uuid
from sqlmodel import SQLModel, Field, Relationship


class User(SQLModel, table=True):
    __tablename__ = "users"
    
    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    email: str = Field(unique=True, index=True, max_length=255)
    password_hash: str = Field(max_length=255)
    created_at: datetime = Field(default_factory=datetime.now)
    
    # Relationships
    contacts: list["Contact"] = Relationship(back_populates="user")


class Contact(SQLModel, table=True):
    __tablename__ = "contacts"
    
    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(max_length=255)
    relationship_type: Optional[str] = Field(default=None, max_length=100)
    birthday: Optional[date] = Field(default=None)
    user_id: uuid.UUID = Field(foreign_key="users.id")
    created_at: datetime = Field(default_factory=datetime.now)
    
    # Relationships
    user: User = Relationship(back_populates="contacts")
    memories: list["Memory"] = Relationship(back_populates="contact")


class Memory(SQLModel, table=True):
    __tablename__ = "memories"
    
    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    content: str
    contact_id: uuid.UUID = Field(foreign_key="contacts.id")
    created_at: datetime = Field(default_factory=datetime.now)
    
    # Relationships
    contact: Contact = Relationship(back_populates="memories")
