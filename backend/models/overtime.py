"""
Overtime tracking models and schemas.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum

from models.base import BaseEntity


class PeriodType(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"


class OvertimeStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    PAID = "paid"


class OvertimeApproval(BaseModel):
    """Overtime approval information."""
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    rejected_reason: Optional[str] = None


# Database Model
class OvertimeRecord(BaseEntity):
    """Overtime record database model."""
    user_id: str
    branch_id: str
    team_id: Optional[str] = None
    
    # Period
    period_type: PeriodType
    period_start: str  # YYYY-MM-DD
    period_end: str    # YYYY-MM-DD
    
    # Overtime details
    threshold_hours: float
    total_worked_hours: float
    overtime_hours: float
    
    # Rate tier (configurable, not hardcoded)
    rate_tier: str
    rate_multiplier: float  # Snapshot at time of calculation
    
    # Associated time entries
    time_entry_ids: List[str] = Field(default_factory=list)
    
    # Approval workflow
    status: OvertimeStatus = OvertimeStatus.PENDING
    requires_approval: bool = True
    approval: OvertimeApproval = Field(default_factory=OvertimeApproval)
    
    # Export tracking
    exported: bool = False
    export_batch_id: Optional[str] = None
    exported_at: Optional[datetime] = None
    
    calculated_at: datetime


# API Schemas
class OvertimeResponse(BaseModel):
    """Schema for overtime record response."""
    id: str
    user_id: str
    branch_id: str
    team_id: Optional[str] = None
    period_type: PeriodType
    period_start: str
    period_end: str
    threshold_hours: float
    total_worked_hours: float
    overtime_hours: float
    rate_tier: str
    rate_multiplier: float
    status: OvertimeStatus
    calculated_at: datetime
    created_at: datetime


class OvertimeListResponse(BaseModel):
    """Schema for paginated overtime list."""
    records: List[OvertimeResponse]
    total: int
    page: int
    page_size: int
    total_overtime_hours: float


class OvertimeSummary(BaseModel):
    """Schema for overtime summary by user."""
    user_id: str
    user_name: str
    total_overtime_hours: float
    pending_hours: float
    approved_hours: float
    records_count: int
