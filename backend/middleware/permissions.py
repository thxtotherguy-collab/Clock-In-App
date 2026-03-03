"""
Permission checking middleware and utilities.
"""
from functools import wraps
from typing import Callable, List, Optional
from fastapi import Depends, HTTPException, status

from core.security import get_current_user, TokenData
from core.exceptions import ForbiddenException
from models.role import (
    has_permission, get_role_data_scope, can_manage_role,
    DataScope
)


def require_permission(permission: str):
    """
    Decorator/dependency to require a specific permission.
    Usage: @router.get("/", dependencies=[Depends(require_permission("users.view_all"))])
    """
    async def permission_checker(
        current_user: TokenData = Depends(get_current_user)
    ):
        if not has_permission(
            current_user.role,
            permission,
            current_user.permissions
        ):
            raise ForbiddenException(
                f"Permission '{permission}' required for this action"
            )
        return current_user
    
    return permission_checker


def require_any_permission(permissions: List[str]):
    """
    Require at least one of the listed permissions.
    """
    async def permission_checker(
        current_user: TokenData = Depends(get_current_user)
    ):
        for perm in permissions:
            if has_permission(current_user.role, perm, current_user.permissions):
                return current_user
        
        raise ForbiddenException(
            f"One of these permissions required: {', '.join(permissions)}"
        )
    
    return permission_checker


def require_all_permissions(permissions: List[str]):
    """
    Require all of the listed permissions.
    """
    async def permission_checker(
        current_user: TokenData = Depends(get_current_user)
    ):
        missing = []
        for perm in permissions:
            if not has_permission(current_user.role, perm, current_user.permissions):
                missing.append(perm)
        
        if missing:
            raise ForbiddenException(
                f"Missing required permissions: {', '.join(missing)}"
            )
        
        return current_user
    
    return permission_checker


class DataScopeFilter:
    """
    Helper class to build data scope filters for queries.
    """
    
    def __init__(self, current_user: TokenData):
        self.user = current_user
        self.scope = get_role_data_scope(current_user.role)
    
    def get_filter(self, user_id_field: str = "user_id") -> dict:
        """
        Get MongoDB filter based on user's data scope.
        """
        if self.scope == DataScope.ALL:
            return {}
        
        if self.scope == DataScope.BRANCH:
            if self.user.branch_id:
                return {"branch_id": self.user.branch_id}
            return {}
        
        if self.scope == DataScope.TEAM:
            if self.user.team_id:
                return {"team_id": self.user.team_id}
            elif self.user.branch_id:
                return {"branch_id": self.user.branch_id}
            return {}
        
        # SELF scope
        return {user_id_field: self.user.user_id}
    
    def can_access_user(self, target_user: dict) -> bool:
        """
        Check if current user can access target user's data.
        """
        if self.scope == DataScope.ALL:
            return True
        
        if self.scope == DataScope.BRANCH:
            return target_user.get("branch_id") == self.user.branch_id
        
        if self.scope == DataScope.TEAM:
            return target_user.get("team_id") == self.user.team_id
        
        # SELF scope
        return target_user.get("id") == self.user.user_id
    
    def can_access_branch(self, branch_id: str) -> bool:
        """
        Check if current user can access a branch.
        """
        if self.scope == DataScope.ALL:
            return True
        
        return branch_id == self.user.branch_id
    
    def can_access_team(self, team_id: str) -> bool:
        """
        Check if current user can access a team.
        """
        if self.scope == DataScope.ALL:
            return True
        
        if self.scope == DataScope.BRANCH:
            # Need to check if team belongs to user's branch
            # This requires a DB lookup - handled at service level
            return True
        
        return team_id == self.user.team_id


def get_data_scope_filter(
    current_user: TokenData = Depends(get_current_user)
) -> DataScopeFilter:
    """
    Dependency to get data scope filter for current user.
    """
    return DataScopeFilter(current_user)
