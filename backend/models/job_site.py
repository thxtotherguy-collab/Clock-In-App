"""
Job Site models and schemas.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

from models.base import AuditableEntity
from models.branch import Address, Geofence


# Database Model
class JobSite(AuditableEntity):
    """Job Site database model."""
    name: str
    code: str
    branch_id: str
    status: str = "active"  # active | inactive | completed
    address: Address = Field(default_factory=Address)
    geofence: Optional[Geofence] = None
    client_name: Optional[str] = None
    project_code: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    assigned_team_ids: List[str] = Field(default_factory=list)


# API Schemas
class JobSiteCreate(BaseModel):
    """Schema for creating a job site."""
    name: str = Field(min_length=1, max_length=200)
    code: str = Field(min_length=1, max_length=50)
    branch_id: str
    address: Optional[Address] = None
    geofence: Optional[Geofence] = None
    client_name: Optional[str] = None
    project_code: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    assigned_team_ids: List[str] = Field(default_factory=list)


class JobSiteUpdate(BaseModel):
    """Schema for updating a job site."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    address: Optional[Address] = None
    geofence: Optional[Geofence] = None
    client_name: Optional[str] = None
    project_code: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    assigned_team_ids: Optional[List[str]] = None
    status: Optional[str] = None


class JobSiteResponse(BaseModel):
    """Schema for job site response."""
    id: str
    name: str
    code: str
    branch_id: str
    status: str
    address: Address
    geofence: Optional[Geofence] = None
    client_name: Optional[str] = None
    project_code: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    assigned_team_ids: List[str]
    created_at: datetime
    updated_at: datetime


class JobSiteListResponse(BaseModel):
    """Schema for paginated job site list."""
    job_sites: List[JobSiteResponse]
    total: int
    page: int
    page_size: int
