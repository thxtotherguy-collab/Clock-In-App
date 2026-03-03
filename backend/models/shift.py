"""
Shift models and schemas.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

from models.base import AuditableEntity


# Database Model
class Shift(AuditableEntity):
    """Shift database model."""
    name: str
    code: str
    branch_id: str
    status: str = "active"
    
    # Timing (local time)
    start_time: str  # HH:MM format
    end_time: str    # HH:MM format
    break_minutes: int = Field(default=60, ge=0)
    total_hours: float
    
    # Days (1=Monday, 7=Sunday)
    days_of_week: List[int] = Field(default_factory=lambda: [1, 2, 3, 4, 5])
    
    # Tolerance
    early_clock_in_minutes: int = Field(default=15, ge=0)
    late_clock_in_minutes: int = Field(default=15, ge=0)
    early_clock_out_minutes: int = Field(default=15, ge=0)


# API Schemas
class ShiftCreate(BaseModel):
    """Schema for creating a shift."""
    name: str = Field(min_length=1, max_length=200)
    code: str = Field(min_length=1, max_length=50)
    branch_id: str
    start_time: str  # HH:MM
    end_time: str    # HH:MM
    break_minutes: int = Field(default=60, ge=0)
    days_of_week: List[int] = Field(default_factory=lambda: [1, 2, 3, 4, 5])
    early_clock_in_minutes: int = Field(default=15, ge=0)
    late_clock_in_minutes: int = Field(default=15, ge=0)
    early_clock_out_minutes: int = Field(default=15, ge=0)


class ShiftUpdate(BaseModel):
    """Schema for updating a shift."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    break_minutes: Optional[int] = Field(None, ge=0)
    days_of_week: Optional[List[int]] = None
    early_clock_in_minutes: Optional[int] = Field(None, ge=0)
    late_clock_in_minutes: Optional[int] = Field(None, ge=0)
    early_clock_out_minutes: Optional[int] = Field(None, ge=0)
    status: Optional[str] = None


class ShiftResponse(BaseModel):
    """Schema for shift response."""
    id: str
    name: str
    code: str
    branch_id: str
    status: str
    start_time: str
    end_time: str
    break_minutes: int
    total_hours: float
    days_of_week: List[int]
    early_clock_in_minutes: int
    late_clock_in_minutes: int
    early_clock_out_minutes: int
    created_at: datetime
    updated_at: datetime


class ShiftListResponse(BaseModel):
    """Schema for shift list."""
    shifts: List[ShiftResponse]
    total: int
