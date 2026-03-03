"""
Audit log models and schemas.
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

from models.base import BaseEntity


# Audit action definitions
AUDIT_ACTIONS = {
    # Authentication
    "auth.login": "User logged in",
    "auth.logout": "User logged out",
    "auth.password_change": "Password changed",
    "auth.password_reset": "Password reset requested",
    "auth.token_refresh": "Token refreshed",
    
    # Users
    "user.create": "User created",
    "user.update": "User updated",
    "user.delete": "User deactivated",
    "user.role_change": "User role changed",
    "user.branch_assign": "User assigned to branch",
    "user.team_assign": "User assigned to team",
    "user.status_change": "User status changed",
    
    # Branches
    "branch.create": "Branch created",
    "branch.update": "Branch updated",
    "branch.delete": "Branch deactivated",
    "branch.settings_change": "Branch settings modified",
    "branch.geofence_update": "Branch geofence updated",
    
    # Teams
    "team.create": "Team created",
    "team.update": "Team updated",
    "team.delete": "Team deactivated",
    "team.member_add": "Member added to team",
    "team.member_remove": "Member removed from team",
    "team.leader_change": "Team leader changed",
    
    # Job Sites
    "job_site.create": "Job site created",
    "job_site.update": "Job site updated",
    "job_site.delete": "Job site deactivated",
    "job_site.complete": "Job site marked complete",
    
    # Time Entries
    "time_entry.clock_in": "Clock in recorded",
    "time_entry.clock_out": "Clock out recorded",
    "time_entry.update": "Time entry modified",
    "time_entry.delete": "Time entry deleted",
    "time_entry.approve": "Time entry approved",
    "time_entry.reject": "Time entry rejected",
    "time_entry.override": "Time entry overridden",
    "time_entry.offline_sync": "Offline entry synced",
    
    # GPS
    "gps.log": "GPS location logged",
    "gps.batch_upload": "GPS batch uploaded",
    "gps.geofence_violation": "Geofence violation detected",
    
    # Overtime
    "overtime.calculate": "Overtime calculated",
    "overtime.approve": "Overtime approved",
    "overtime.reject": "Overtime rejected",
    "overtime.export": "Overtime exported",
    
    # Reports
    "report.generate": "Report generated",
    "report.export": "Report exported",
    "report.schedule_create": "Report schedule created",
    "report.schedule_update": "Report schedule updated",
    
    # Settings
    "settings.update": "System settings updated",
    "rate_config.create": "Rate configuration created",
    "rate_config.update": "Rate configuration updated",
    
    # Shifts
    "shift.create": "Shift created",
    "shift.update": "Shift updated",
    "shift.delete": "Shift deactivated",
}


class AuditChanges(BaseModel):
    """Audit change tracking."""
    before: Dict[str, Any] = Field(default_factory=dict)
    after: Dict[str, Any] = Field(default_factory=dict)


# Database Model
class AuditLog(BaseEntity):
    """Audit log database model."""
    # Who
    actor_id: str
    actor_email: str
    actor_role: str
    actor_ip: Optional[str] = None
    actor_device: Optional[str] = None
    
    # What
    action: str
    action_category: str
    description: str
    
    # Target
    target_type: str
    target_id: str
    target_ref: Optional[str] = None  # Human readable reference
    
    # Context
    branch_id: Optional[str] = None
    team_id: Optional[str] = None
    
    # Changes
    changes: Optional[AuditChanges] = None
    
    # Additional metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Timestamp
    timestamp: datetime


# API Schemas
class AuditLogResponse(BaseModel):
    """Schema for audit log response."""
    id: str
    actor_id: str
    actor_email: str
    actor_role: str
    action: str
    action_category: str
    description: str
    target_type: str
    target_id: str
    target_ref: Optional[str] = None
    branch_id: Optional[str] = None
    changes: Optional[AuditChanges] = None
    timestamp: datetime


class AuditLogListResponse(BaseModel):
    """Schema for paginated audit log list."""
    logs: List[AuditLogResponse]
    total: int
    page: int
    page_size: int


class AuditLogFilter(BaseModel):
    """Schema for audit log filtering."""
    actor_id: Optional[str] = None
    action_category: Optional[str] = None
    target_type: Optional[str] = None
    target_id: Optional[str] = None
    branch_id: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


def get_action_description(action: str) -> str:
    """Get human-readable description for an action."""
    return AUDIT_ACTIONS.get(action, action)
