"""
Models module initialization.
"""
from models.base import BaseEntity, AuditableEntity, SoftDeleteEntity
from models.user import (
    User, UserCreate, UserUpdate, UserResponse, UserListResponse,
    UserRole, UserStatus
)
from models.role import (
    Role, RoleResponse, DataScope,
    ROLE_PERMISSIONS, ROLE_DATA_SCOPE, ROLE_LEVELS,
    get_role_permissions, get_role_data_scope, get_role_level,
    has_permission, can_manage_role
)
from models.branch import (
    Branch, BranchCreate, BranchUpdate, BranchResponse, BranchListResponse,
    GeoPoint, Geofence, Address, BranchSettings
)
from models.team import (
    Team, TeamCreate, TeamUpdate, TeamResponse, TeamListResponse,
    TeamSettings
)
from models.job_site import (
    JobSite, JobSiteCreate, JobSiteUpdate, JobSiteResponse, JobSiteListResponse
)
from models.time_entry import (
    TimeEntry, ClockInRequest, ClockOutRequest, TimeEntryOverride,
    TimeEntryResponse, TimeEntryListResponse, TodayStatusResponse,
    PunchMethod, TimeEntryStatus, GPSData, DeviceInfo, PunchData,
    Approval, OfflineSync, TimeEntryFlags
)
from models.gps import (
    GPSLog, GPSLogCreate, GPSBatchCreate, GPSLogResponse,
    GPSTrackResponse, LiveLocationResponse, GeoJSONPoint
)
from models.overtime import (
    OvertimeRecord, OvertimeResponse, OvertimeListResponse, OvertimeSummary,
    PeriodType, OvertimeStatus, OvertimeApproval
)
from models.audit import (
    AuditLog, AuditLogResponse, AuditLogListResponse, AuditLogFilter,
    AuditChanges, AUDIT_ACTIONS, get_action_description
)
from models.rate_config import (
    RateConfiguration, RateConfigCreate, RateConfigUpdate,
    RateConfigResponse, RateConfigListResponse, RateTier
)
from models.shift import (
    Shift, ShiftCreate, ShiftUpdate, ShiftResponse, ShiftListResponse
)
from models.report import (
    Report, ReportCreate, ReportUpdate, ReportResponse, ReportListResponse,
    ReportRunResponse, ReportType, ReportFormat, ScheduleFrequency,
    ScopeLevel, ReportScope, DateRangeFilter, ReportFilters,
    ReportOutput, ReportSchedule, LastRun, ReportVisibility
)

__all__ = [
    # Base
    "BaseEntity", "AuditableEntity", "SoftDeleteEntity",
    # User
    "User", "UserCreate", "UserUpdate", "UserResponse", "UserListResponse",
    "UserRole", "UserStatus",
    # Role
    "Role", "RoleResponse", "DataScope",
    "ROLE_PERMISSIONS", "ROLE_DATA_SCOPE", "ROLE_LEVELS",
    "get_role_permissions", "get_role_data_scope", "get_role_level",
    "has_permission", "can_manage_role",
    # Branch
    "Branch", "BranchCreate", "BranchUpdate", "BranchResponse", "BranchListResponse",
    "GeoPoint", "Geofence", "Address", "BranchSettings",
    # Team
    "Team", "TeamCreate", "TeamUpdate", "TeamResponse", "TeamListResponse",
    "TeamSettings",
    # Job Site
    "JobSite", "JobSiteCreate", "JobSiteUpdate", "JobSiteResponse", "JobSiteListResponse",
    # Time Entry
    "TimeEntry", "ClockInRequest", "ClockOutRequest", "TimeEntryOverride",
    "TimeEntryResponse", "TimeEntryListResponse", "TodayStatusResponse",
    "PunchMethod", "TimeEntryStatus", "GPSData", "DeviceInfo", "PunchData",
    "Approval", "OfflineSync", "TimeEntryFlags",
    # GPS
    "GPSLog", "GPSLogCreate", "GPSBatchCreate", "GPSLogResponse",
    "GPSTrackResponse", "LiveLocationResponse", "GeoJSONPoint",
    # Overtime
    "OvertimeRecord", "OvertimeResponse", "OvertimeListResponse", "OvertimeSummary",
    "PeriodType", "OvertimeStatus", "OvertimeApproval",
    # Audit
    "AuditLog", "AuditLogResponse", "AuditLogListResponse", "AuditLogFilter",
    "AuditChanges", "AUDIT_ACTIONS", "get_action_description",
    # Rate Config
    "RateConfiguration", "RateConfigCreate", "RateConfigUpdate",
    "RateConfigResponse", "RateConfigListResponse", "RateTier",
    # Shift
    "Shift", "ShiftCreate", "ShiftUpdate", "ShiftResponse", "ShiftListResponse",
    # Report
    "Report", "ReportCreate", "ReportUpdate", "ReportResponse", "ReportListResponse",
    "ReportRunResponse", "ReportType", "ReportFormat", "ScheduleFrequency",
    "ScopeLevel", "ReportScope", "DateRangeFilter", "ReportFilters",
    "ReportOutput", "ReportSchedule", "LastRun", "ReportVisibility",
]
