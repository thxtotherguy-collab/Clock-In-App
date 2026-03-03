"""
Base model with common fields for all entities.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime, timezone
import uuid


def generate_uuid() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class BaseEntity(BaseModel):
    """Base entity with common fields."""
    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={datetime: lambda v: v.isoformat()}
    )
    
    id: str = Field(default_factory=generate_uuid)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class AuditableEntity(BaseEntity):
    """Entity with audit fields."""
    created_by: Optional[str] = None
    updated_by: Optional[str] = None


class SoftDeleteEntity(AuditableEntity):
    """Entity with soft delete support."""
    status: str = "active"
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[str] = None
