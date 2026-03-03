"""
User models and schemas.
"""
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum

from models.base import SoftDeleteEntity, generate_uuid, utc_now


class UserRole(str, Enum):
    SUPER_ADMIN = "SUPER_ADMIN"
    BRANCH_ADMIN = "BRANCH_ADMIN"
    TEAM_LEADER = "TEAM_LEADER"
    WORKER = "WORKER"


class UserStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


# Database Model
class User(SoftDeleteEntity):
    """User database model."""
    email: EmailStr
    password_hash: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    employee_id: Optional[str] = None
    role: UserRole = UserRole.WORKER
    status: UserStatus = UserStatus.ACTIVE
    
    # Assignments
    branch_id: Optional[str] = None
    team_id: Optional[str] = None
    job_site_ids: List[str] = Field(default_factory=list)
    
    # Profile
    profile_photo_url: Optional[str] = None
    date_of_birth: Optional[str] = None
    hire_date: Optional[str] = None
    termination_date: Optional[str] = None
    
    # Work settings
    hourly_rate_tier: str = "standard"
    overtime_eligible: bool = True
    default_shift_id: Optional[str] = None
    
    # Permissions override
    permission_overrides: Dict[str, bool] = Field(default_factory=dict)
    
    # Metadata
    last_login_at: Optional[datetime] = None


# API Schemas
class UserCreate(BaseModel):
    """Schema for creating a user."""
    email: EmailStr
    password: str = Field(min_length=8)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    phone: Optional[str] = None
    employee_id: Optional[str] = None
    role: UserRole = UserRole.WORKER
    branch_id: Optional[str] = None
    team_id: Optional[str] = None
    job_site_ids: List[str] = Field(default_factory=list)
    hourly_rate_tier: str = "standard"
    overtime_eligible: bool = True
    default_shift_id: Optional[str] = None


class UserUpdate(BaseModel):
    """Schema for updating a user."""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone: Optional[str] = None
    employee_id: Optional[str] = None
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None
    branch_id: Optional[str] = None
    team_id: Optional[str] = None
    job_site_ids: Optional[List[str]] = None
    profile_photo_url: Optional[str] = None
    date_of_birth: Optional[str] = None
    hire_date: Optional[str] = None
    termination_date: Optional[str] = None
    hourly_rate_tier: Optional[str] = None
    overtime_eligible: Optional[bool] = None
    default_shift_id: Optional[str] = None
    permission_overrides: Optional[Dict[str, bool]] = None


class UserResponse(BaseModel):
    """Schema for user response (excludes sensitive data)."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    email: EmailStr
    first_name: str
    last_name: str
    phone: Optional[str] = None
    employee_id: Optional[str] = None
    role: UserRole
    status: UserStatus
    branch_id: Optional[str] = None
    team_id: Optional[str] = None
    job_site_ids: List[str] = Field(default_factory=list)
    profile_photo_url: Optional[str] = None
    date_of_birth: Optional[str] = None
    hire_date: Optional[str] = None
    hourly_rate_tier: str = "standard"
    overtime_eligible: bool = True
    default_shift_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime] = None


class UserListResponse(BaseModel):
    """Schema for paginated user list."""
    users: List[UserResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
