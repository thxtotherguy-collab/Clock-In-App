"""
Time Entry (Clock-in/out) models and schemas.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

from models.base import BaseEntity, generate_uuid, utc_now


class PunchMethod(str, Enum):
    MOBILE_APP = "mobile_app"
    WEB = "web"
    MANUAL = "manual"
    KIOSK = "kiosk"


class TimeEntryStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    APPROVED = "approved"
    REJECTED = "rejected"


class GPSData(BaseModel):
    """GPS location data for a punch."""
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    accuracy_meters: Optional[float] = None
    altitude_meters: Optional[float] = None
    captured_at: datetime
    provider: str = "gps"  # gps | network | fused


class DeviceInfo(BaseModel):
    """Device information for punch."""
    device_id: Optional[str] = None
    platform: Optional[str] = None  # ios | android | web
    os_version: Optional[str] = None
    app_version: Optional[str] = None
    device_model: Optional[str] = None


class GeofenceValidation(BaseModel):
    """Geofence validation result."""
    within_geofence: bool
    distance_from_center_meters: Optional[float] = None
    validated_against: str = "branch"  # branch | job_site
    geofence_id: Optional[str] = None


class PunchData(BaseModel):
    """Clock in/out punch data."""
    timestamp: datetime
    local_time: Optional[str] = None
    gps: Optional[GPSData] = None
    photo_url: Optional[str] = None
    method: PunchMethod = PunchMethod.MOBILE_APP
    device_info: Optional[DeviceInfo] = None
    within_geofence: Optional[bool] = None
    geofence_distance_meters: Optional[float] = None


class Approval(BaseModel):
    """Approval information."""
    required: bool = False
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    notes: Optional[str] = None


class OfflineSync(BaseModel):
    """Offline sync tracking."""
    is_offline_entry: bool = False
    offline_id: Optional[str] = None
    synced_at: Optional[datetime] = None
    sync_conflicts: List[Dict[str, Any]] = Field(default_factory=list)


class TimeEntryFlags(BaseModel):
    """Time entry flags for alerts/notifications."""
    late_clock_in: bool = False
    early_clock_out: bool = False
    missing_clock_out: bool = False
    outside_geofence: bool = False
    overtime_flagged: bool = False


# Database Model
class TimeEntry(BaseEntity):
    """Time Entry database model."""
    user_id: str
    branch_id: str
    team_id: Optional[str] = None
    job_site_id: Optional[str] = None
    
    # Date for easy querying
    date: str  # YYYY-MM-DD
    
    # Punch data
    clock_in: Optional[PunchData] = None
    clock_out: Optional[PunchData] = None
    
    # Calculated fields
    total_hours: Optional[float] = None
    regular_hours: Optional[float] = None
    overtime_hours: Optional[float] = None
    break_minutes: int = 0
    
    # Status
    status: TimeEntryStatus = TimeEntryStatus.PENDING
    approval: Approval = Field(default_factory=Approval)
    
    # Offline sync
    offline_sync: OfflineSync = Field(default_factory=OfflineSync)
    
    # Override tracking
    is_manual_entry: bool = False
    original_values: Optional[Dict[str, Any]] = None
    edited_by: Optional[str] = None
    edited_at: Optional[datetime] = None
    edit_reason: Optional[str] = None
    
    # Flags
    flags: TimeEntryFlags = Field(default_factory=TimeEntryFlags)


# API Schemas
class ClockInRequest(BaseModel):
    """Schema for clock in request."""
    job_site_id: Optional[str] = None
    gps: Optional[GPSData] = None
    photo_url: Optional[str] = None
    method: PunchMethod = PunchMethod.MOBILE_APP
    device_info: Optional[DeviceInfo] = None
    # Offline sync fields
    offline_id: Optional[str] = None
    offline_timestamp: Optional[datetime] = None


class ClockOutRequest(BaseModel):
    """Schema for clock out request."""
    gps: Optional[GPSData] = None
    photo_url: Optional[str] = None
    method: PunchMethod = PunchMethod.MOBILE_APP
    device_info: Optional[DeviceInfo] = None
    break_minutes: int = 0
    # Offline sync fields
    offline_id: Optional[str] = None
    offline_timestamp: Optional[datetime] = None


class TimeEntryOverride(BaseModel):
    """Schema for manually overriding a time entry."""
    clock_in_timestamp: Optional[datetime] = None
    clock_out_timestamp: Optional[datetime] = None
    break_minutes: Optional[int] = None
    job_site_id: Optional[str] = None
    reason: str = Field(min_length=1)


class TimeEntryResponse(BaseModel):
    """Schema for time entry response."""
    id: str
    user_id: str
    branch_id: str
    team_id: Optional[str] = None
    job_site_id: Optional[str] = None
    date: str
    clock_in: Optional[PunchData] = None
    clock_out: Optional[PunchData] = None
    total_hours: Optional[float] = None
    regular_hours: Optional[float] = None
    overtime_hours: Optional[float] = None
    break_minutes: int
    status: TimeEntryStatus
    flags: TimeEntryFlags
    is_manual_entry: bool
    created_at: datetime
    updated_at: datetime


class TimeEntryListResponse(BaseModel):
    """Schema for paginated time entry list."""
    entries: List[TimeEntryResponse]
    total: int
    page: int
    page_size: int


class TodayStatusResponse(BaseModel):
    """Schema for today's attendance status."""
    is_clocked_in: bool
    current_entry: Optional[TimeEntryResponse] = None
    total_hours_today: float = 0.0
    entries_today: int = 0
