"""
Report models and schemas.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

from models.base import AuditableEntity


class ReportType(str, Enum):
    ATTENDANCE_SUMMARY = "attendance_summary"
    OVERTIME = "overtime"
    LATE_ARRIVALS = "late_arrivals"
    PAYROLL = "payroll"
    BRANCH_PERFORMANCE = "branch_performance"
    GPS_TRACKING = "gps_tracking"
    CUSTOM = "custom"


class ReportFormat(str, Enum):
    CSV = "csv"
    XLSX = "xlsx"
    PDF = "pdf"


class ScheduleFrequency(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class ScopeLevel(str, Enum):
    SELF = "self"
    TEAM = "team"
    BRANCH = "branch"
    ALL = "all"


class ReportScope(BaseModel):
    """Report scope configuration."""
    level: ScopeLevel
    branch_id: Optional[str] = None
    team_id: Optional[str] = None
    user_ids: List[str] = Field(default_factory=list)


class DateRangeFilter(BaseModel):
    """Date range filter."""
    type: str = "relative"  # relative | absolute
    relative_days: Optional[int] = 7
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class ReportFilters(BaseModel):
    """Report filters."""
    date_range: DateRangeFilter = Field(default_factory=DateRangeFilter)
    include_overtime: bool = True
    include_late_arrivals: bool = True
    status_filter: List[str] = Field(default_factory=lambda: ["completed", "approved"])


class ReportOutput(BaseModel):
    """Report output configuration."""
    format: ReportFormat = ReportFormat.XLSX
    columns: List[str] = Field(default_factory=list)
    group_by: Optional[str] = None
    sort_by: Optional[str] = None


class ReportSchedule(BaseModel):
    """Report schedule configuration."""
    enabled: bool = False
    frequency: ScheduleFrequency = ScheduleFrequency.WEEKLY
    day_of_week: Optional[int] = 1  # Monday
    day_of_month: Optional[int] = None
    time: str = "06:00"
    timezone: str = "America/New_York"
    recipients: List[str] = Field(default_factory=list)


class LastRun(BaseModel):
    """Last run information."""
    timestamp: Optional[datetime] = None
    status: str = "never"
    file_url: Optional[str] = None
    record_count: int = 0


class ReportVisibility(str, Enum):
    PRIVATE = "private"
    TEAM = "team"
    BRANCH = "branch"
    ALL = "all"


# Database Model
class Report(AuditableEntity):
    """Report database model."""
    name: str
    type: ReportType
    scope: ReportScope
    filters: ReportFilters = Field(default_factory=ReportFilters)
    output: ReportOutput = Field(default_factory=ReportOutput)
    schedule: ReportSchedule = Field(default_factory=ReportSchedule)
    last_run: LastRun = Field(default_factory=LastRun)
    visibility: ReportVisibility = ReportVisibility.PRIVATE


# API Schemas
class ReportCreate(BaseModel):
    """Schema for creating a report."""
    name: str = Field(min_length=1, max_length=200)
    type: ReportType
    scope: ReportScope
    filters: Optional[ReportFilters] = None
    output: Optional[ReportOutput] = None
    schedule: Optional[ReportSchedule] = None
    visibility: ReportVisibility = ReportVisibility.PRIVATE


class ReportUpdate(BaseModel):
    """Schema for updating a report."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    filters: Optional[ReportFilters] = None
    output: Optional[ReportOutput] = None
    schedule: Optional[ReportSchedule] = None
    visibility: Optional[ReportVisibility] = None


class ReportResponse(BaseModel):
    """Schema for report response."""
    id: str
    name: str
    type: ReportType
    scope: ReportScope
    filters: ReportFilters
    output: ReportOutput
    schedule: ReportSchedule
    last_run: LastRun
    visibility: ReportVisibility
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ReportListResponse(BaseModel):
    """Schema for report list."""
    reports: List[ReportResponse]
    total: int


class ReportRunResponse(BaseModel):
    """Schema for report run response."""
    report_id: str
    status: str
    file_url: Optional[str] = None
    record_count: int
    generated_at: datetime
