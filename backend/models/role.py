"""
Role models and permission definitions.
"""
from pydantic import BaseModel, Field
from typing import Dict, List
from enum import Enum

from models.base import BaseEntity


class DataScope(str, Enum):
    SELF = "self"
    TEAM = "team"
    BRANCH = "branch"
    ALL = "all"


# Permission definitions
ROLE_PERMISSIONS = {
    "SUPER_ADMIN": {
        # Full access to everything
        "users.view_self": True,
        "users.view_team": True,
        "users.view_branch": True,
        "users.view_all": True,
        "users.create": True,
        "users.update_self": True,
        "users.update_others": True,
        "users.delete": True,
        
        "branches.view_assigned": True,
        "branches.view_all": True,
        "branches.create": True,
        "branches.update": True,
        "branches.delete": True,
        
        "teams.view_assigned": True,
        "teams.view_branch": True,
        "teams.view_all": True,
        "teams.create": True,
        "teams.update": True,
        "teams.delete": True,
        
        "job_sites.view_assigned": True,
        "job_sites.view_all": True,
        "job_sites.create": True,
        "job_sites.update": True,
        "job_sites.delete": True,
        
        "time_entries.punch_self": True,
        "time_entries.view_self": True,
        "time_entries.view_team": True,
        "time_entries.view_branch": True,
        "time_entries.view_all": True,
        "time_entries.override": True,
        "time_entries.approve": True,
        "time_entries.delete": True,
        
        "reports.view_self": True,
        "reports.view_team": True,
        "reports.view_branch": True,
        "reports.view_all": True,
        "reports.export": True,
        "reports.create": True,
        "reports.schedule": True,
        
        "overtime.view_self": True,
        "overtime.view_team": True,
        "overtime.view_branch": True,
        "overtime.view_all": True,
        "overtime.approve": True,
        
        "audit.view": True,
        "audit.export": True,
        
        "settings.view": True,
        "settings.update": True,
        "rate_config.view": True,
        "rate_config.update": True,
    },
    
    "BRANCH_ADMIN": {
        "users.view_self": True,
        "users.view_team": True,
        "users.view_branch": True,
        "users.view_all": False,
        "users.create": True,
        "users.update_self": True,
        "users.update_others": True,  # Within branch
        "users.delete": True,  # Within branch
        
        "branches.view_assigned": True,
        "branches.view_all": False,
        "branches.create": False,
        "branches.update": True,  # Own branch only
        "branches.delete": False,
        
        "teams.view_assigned": True,
        "teams.view_branch": True,
        "teams.view_all": False,
        "teams.create": True,
        "teams.update": True,
        "teams.delete": True,
        
        "job_sites.view_assigned": True,
        "job_sites.view_all": False,
        "job_sites.create": True,
        "job_sites.update": True,
        "job_sites.delete": True,
        
        "time_entries.punch_self": True,
        "time_entries.view_self": True,
        "time_entries.view_team": True,
        "time_entries.view_branch": True,
        "time_entries.view_all": False,
        "time_entries.override": True,
        "time_entries.approve": True,
        "time_entries.delete": True,
        
        "reports.view_self": True,
        "reports.view_team": True,
        "reports.view_branch": True,
        "reports.view_all": False,
        "reports.export": True,
        "reports.create": True,
        "reports.schedule": True,
        
        "overtime.view_self": True,
        "overtime.view_team": True,
        "overtime.view_branch": True,
        "overtime.view_all": False,
        "overtime.approve": True,
        
        "audit.view": True,  # Branch audit only
        "audit.export": True,
        
        "settings.view": True,
        "settings.update": False,
        "rate_config.view": True,
        "rate_config.update": False,
    },
    
    "TEAM_LEADER": {
        "users.view_self": True,
        "users.view_team": True,
        "users.view_branch": False,
        "users.view_all": False,
        "users.create": False,
        "users.update_self": True,
        "users.update_others": False,
        "users.delete": False,
        
        "branches.view_assigned": True,
        "branches.view_all": False,
        "branches.create": False,
        "branches.update": False,
        "branches.delete": False,
        
        "teams.view_assigned": True,
        "teams.view_branch": False,
        "teams.view_all": False,
        "teams.create": False,
        "teams.update": True,  # Own team only
        "teams.delete": False,
        
        "job_sites.view_assigned": True,
        "job_sites.view_all": False,
        "job_sites.create": False,
        "job_sites.update": False,
        "job_sites.delete": False,
        
        "time_entries.punch_self": True,
        "time_entries.view_self": True,
        "time_entries.view_team": True,
        "time_entries.view_branch": False,
        "time_entries.view_all": False,
        "time_entries.override": True,  # Team only
        "time_entries.approve": True,   # Team only
        "time_entries.delete": False,
        
        "reports.view_self": True,
        "reports.view_team": True,
        "reports.view_branch": False,
        "reports.view_all": False,
        "reports.export": True,
        "reports.create": False,
        "reports.schedule": False,
        
        "overtime.view_self": True,
        "overtime.view_team": True,
        "overtime.view_branch": False,
        "overtime.view_all": False,
        "overtime.approve": True,  # Team only
        
        "audit.view": False,
        "audit.export": False,
        
        "settings.view": False,
        "settings.update": False,
        "rate_config.view": False,
        "rate_config.update": False,
    },
    
    "WORKER": {
        "users.view_self": True,
        "users.view_team": False,
        "users.view_branch": False,
        "users.view_all": False,
        "users.create": False,
        "users.update_self": True,
        "users.update_others": False,
        "users.delete": False,
        
        "branches.view_assigned": True,
        "branches.view_all": False,
        "branches.create": False,
        "branches.update": False,
        "branches.delete": False,
        
        "teams.view_assigned": True,
        "teams.view_branch": False,
        "teams.view_all": False,
        "teams.create": False,
        "teams.update": False,
        "teams.delete": False,
        
        "job_sites.view_assigned": True,
        "job_sites.view_all": False,
        "job_sites.create": False,
        "job_sites.update": False,
        "job_sites.delete": False,
        
        "time_entries.punch_self": True,
        "time_entries.view_self": True,
        "time_entries.view_team": False,
        "time_entries.view_branch": False,
        "time_entries.view_all": False,
        "time_entries.override": False,
        "time_entries.approve": False,
        "time_entries.delete": False,
        
        "reports.view_self": True,
        "reports.view_team": False,
        "reports.view_branch": False,
        "reports.view_all": False,
        "reports.export": False,
        "reports.create": False,
        "reports.schedule": False,
        
        "overtime.view_self": True,
        "overtime.view_team": False,
        "overtime.view_branch": False,
        "overtime.view_all": False,
        "overtime.approve": False,
        
        "audit.view": False,
        "audit.export": False,
        
        "settings.view": False,
        "settings.update": False,
        "rate_config.view": False,
        "rate_config.update": False,
    }
}


# Data scope per role
ROLE_DATA_SCOPE = {
    "SUPER_ADMIN": DataScope.ALL,
    "BRANCH_ADMIN": DataScope.BRANCH,
    "TEAM_LEADER": DataScope.TEAM,
    "WORKER": DataScope.SELF
}


# Role hierarchy levels
ROLE_LEVELS = {
    "SUPER_ADMIN": 100,
    "BRANCH_ADMIN": 75,
    "TEAM_LEADER": 50,
    "WORKER": 25
}


class Role(BaseEntity):
    """Role database model."""
    name: str
    display_name: str
    description: str
    level: int
    permissions: Dict[str, bool]
    data_scope: DataScope


class RoleResponse(BaseModel):
    """Schema for role response."""
    name: str
    display_name: str
    description: str
    level: int
    data_scope: DataScope
    permissions: Dict[str, bool]


def get_role_permissions(role_name: str) -> Dict[str, bool]:
    """Get permissions for a role."""
    return ROLE_PERMISSIONS.get(role_name, {})


def get_role_data_scope(role_name: str) -> DataScope:
    """Get data scope for a role."""
    return ROLE_DATA_SCOPE.get(role_name, DataScope.SELF)


def get_role_level(role_name: str) -> int:
    """Get hierarchy level for a role."""
    return ROLE_LEVELS.get(role_name, 0)


def has_permission(role_name: str, permission: str, overrides: Dict[str, bool] = None) -> bool:
    """Check if a role has a specific permission."""
    # Check overrides first
    if overrides and permission in overrides:
        return overrides[permission]
    
    # Then check role permissions
    permissions = get_role_permissions(role_name)
    return permissions.get(permission, False)


def can_manage_role(manager_role: str, target_role: str) -> bool:
    """Check if one role can manage another role."""
    manager_level = get_role_level(manager_role)
    target_level = get_role_level(target_role)
    return manager_level > target_level
