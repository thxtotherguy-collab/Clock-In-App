"""
Audit logs viewing router - Admin access to audit trail.
"""
from fastapi import APIRouter, Depends, Query
from datetime import datetime, timezone
from typing import Optional

from core.database import get_database
from core.security import get_current_user, TokenData
from core.exceptions import ForbiddenException
from models.role import has_permission, get_role_data_scope, DataScope
from services.audit_service import AuditService

router = APIRouter(prefix="/admin/audit-logs", tags=["Audit Logs"])


@router.get("/list")
async def list_audit_logs(
    action_category: Optional[str] = None,
    target_type: Optional[str] = None,
    actor_id: Optional[str] = None,
    branch_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: TokenData = Depends(get_current_user)
):
    """List audit logs with filtering."""
    db = get_database()

    if not has_permission(current_user.role, "audit.view"):
        raise ForbiddenException("Cannot view audit logs")

    scope = get_role_data_scope(current_user.role)

    # Build query
    query = {}

    # Scope restrictions
    if scope == DataScope.BRANCH:
        query["branch_id"] = current_user.branch_id
    elif scope == DataScope.TEAM:
        query["team_id"] = current_user.team_id

    if action_category:
        query["action_category"] = action_category
    if target_type:
        query["target_type"] = target_type
    if actor_id:
        query["actor_id"] = actor_id
    if branch_id and scope == DataScope.ALL:
        query["branch_id"] = branch_id

    if start_date or end_date:
        query["timestamp"] = {}
        if start_date:
            query["timestamp"]["$gte"] = start_date
        if end_date:
            query["timestamp"]["$lte"] = end_date + "T23:59:59"

    # Get total count
    total = await db.audit_logs.count_documents(query)

    # Get paginated results
    skip = (page - 1) * page_size
    logs = await db.audit_logs.find(query, {"_id": 0}) \
        .sort("timestamp", -1) \
        .skip(skip) \
        .limit(page_size) \
        .to_list(page_size)

    return {
        "logs": logs,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }


@router.get("/categories")
async def get_audit_categories(
    current_user: TokenData = Depends(get_current_user)
):
    """Get available audit action categories."""
    if not has_permission(current_user.role, "audit.view"):
        raise ForbiddenException("Cannot view audit logs")

    return {
        "categories": [
            {"value": "time_entry", "label": "Time Entries"},
            {"value": "user", "label": "Users"},
            {"value": "branch", "label": "Branches"},
            {"value": "report", "label": "Reports/Exports"},
        ],
        "target_types": [
            {"value": "time_entry", "label": "Time Entry"},
            {"value": "user", "label": "User"},
            {"value": "branch", "label": "Branch"},
            {"value": "timesheet", "label": "Timesheet"},
            {"value": "payroll", "label": "Payroll"},
        ]
    }
