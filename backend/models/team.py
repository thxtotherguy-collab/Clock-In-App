"""
Team models and schemas.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime

from models.base import AuditableEntity


class TeamSettings(BaseModel):
    """Team-specific settings."""
    default_job_site_id: Optional[str] = None
    default_shift_id: Optional[str] = None


# Database Model
class Team(AuditableEntity):
    """Team database model."""
    name: str
    code: str
    branch_id: str
    status: str = "active"
    leader_id: Optional[str] = None
    supervisor_ids: List[str] = Field(default_factory=list)
    settings: TeamSettings = Field(default_factory=TeamSettings)


# API Schemas
class TeamCreate(BaseModel):
    """Schema for creating a team."""
    name: str = Field(min_length=1, max_length=200)
    code: str = Field(min_length=1, max_length=50)
    branch_id: str
    leader_id: Optional[str] = None
    supervisor_ids: List[str] = Field(default_factory=list)
    settings: Optional[TeamSettings] = None


class TeamUpdate(BaseModel):
    """Schema for updating a team."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    leader_id: Optional[str] = None
    supervisor_ids: Optional[List[str]] = None
    settings: Optional[TeamSettings] = None
    status: Optional[str] = None


class TeamResponse(BaseModel):
    """Schema for team response."""
    id: str
    name: str
    code: str
    branch_id: str
    status: str
    leader_id: Optional[str] = None
    supervisor_ids: List[str]
    settings: TeamSettings
    created_at: datetime
    updated_at: datetime


class TeamListResponse(BaseModel):
    """Schema for paginated team list."""
    teams: List[TeamResponse]
    total: int
    page: int
    page_size: int
