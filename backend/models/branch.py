"""
Branch models and schemas.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime

from models.base import AuditableEntity


class GeoPoint(BaseModel):
    """Geographic point."""
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class Geofence(BaseModel):
    """Geofence configuration."""
    center: GeoPoint
    radius_meters: int = Field(default=150, ge=10, le=10000)
    type: str = "circle"  # circle | polygon (future)


class Address(BaseModel):
    """Address model."""
    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: str = "US"


class BranchSettings(BaseModel):
    """Branch-specific settings."""
    punch_tolerance_minutes: int = Field(default=15, ge=0, le=60)
    require_gps_for_punch: bool = True
    require_photo_for_punch: bool = False
    allow_offline_punch: bool = True
    auto_clock_out_hours: int = Field(default=12, ge=1, le=24)
    overtime_threshold_daily: float = Field(default=8.0, ge=0)
    overtime_threshold_weekly: float = Field(default=40.0, ge=0)


# Database Model
class Branch(AuditableEntity):
    """Branch database model."""
    name: str
    code: str
    status: str = "active"
    address: Address = Field(default_factory=Address)
    geofence: Optional[Geofence] = None
    timezone: str = "America/New_York"
    settings: BranchSettings = Field(default_factory=BranchSettings)
    admin_ids: List[str] = Field(default_factory=list)


# API Schemas
class BranchCreate(BaseModel):
    """Schema for creating a branch."""
    name: str = Field(min_length=1, max_length=200)
    code: str = Field(min_length=1, max_length=50)
    address: Optional[Address] = None
    geofence: Optional[Geofence] = None
    timezone: str = "America/New_York"
    settings: Optional[BranchSettings] = None
    admin_ids: List[str] = Field(default_factory=list)


class BranchUpdate(BaseModel):
    """Schema for updating a branch."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    address: Optional[Address] = None
    geofence: Optional[Geofence] = None
    timezone: Optional[str] = None
    settings: Optional[BranchSettings] = None
    admin_ids: Optional[List[str]] = None
    status: Optional[str] = None


class BranchResponse(BaseModel):
    """Schema for branch response."""
    id: str
    name: str
    code: str
    status: str
    address: Address
    geofence: Optional[Geofence] = None
    timezone: str
    settings: BranchSettings
    admin_ids: List[str]
    created_at: datetime
    updated_at: datetime


class BranchListResponse(BaseModel):
    """Schema for paginated branch list."""
    branches: List[BranchResponse]
    total: int
    page: int
    page_size: int
