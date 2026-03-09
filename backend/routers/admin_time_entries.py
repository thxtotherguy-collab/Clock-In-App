"""
Time entries management router - Admin functions for viewing, editing, approving.
"""
from fastapi import APIRouter, Depends, Query, Request
from datetime import datetime, timezone
from typing import Optional, List
from pydantic import BaseModel

from core.database import get_database
from core.security import get_current_user, TokenData
from core.exceptions import ForbiddenException, NotFoundException, BadRequestException
from middleware.permissions import require_permission, DataScopeFilter
from models.role import has_permission, get_role_data_scope, DataScope
from models.base import utc_now
from services.audit_service import audit_log

router = APIRouter(prefix="/admin/time-entries", tags=["Time Entry Management"])


class TimeEntryEdit(BaseModel):
    clock_in_time: Optional[str] = None
    clock_out_time: Optional[str] = None
    break_minutes: Optional[int] = None
    job_site_id: Optional[str] = None
    reason: str


class ApprovalAction(BaseModel):
    action: str  # approve | reject
    notes: Optional[str] = None


class BulkApproval(BaseModel):
    entry_ids: List[str]
    action: str  # approve | reject
    notes: Optional[str] = None


@router.get("/list")
async def list_time_entries(
    branch_id: Optional[str] = None,
    team_id: Optional[str] = None,
    user_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: TokenData = Depends(get_current_user)
):
    """List time entries with filtering (admin view)."""
    db = get_database()
    
    if not has_permission(current_user.role, "time_entries.view_branch"):
        if not has_permission(current_user.role, "time_entries.view_team"):
            raise ForbiddenException("Insufficient permissions")
    
    scope = get_role_data_scope(current_user.role)
    
    # Build query
    query = {}
    
    # Apply scope restrictions
    if scope == DataScope.BRANCH:
        query["branch_id"] = current_user.branch_id
    elif scope == DataScope.TEAM:
        query["team_id"] = current_user.team_id
    elif scope == DataScope.SELF:
        query["user_id"] = current_user.user_id
    
    # Apply filters (if allowed by scope)
    if branch_id and scope == DataScope.ALL:
        query["branch_id"] = branch_id
    if team_id:
        query["team_id"] = team_id
    if user_id:
        query["user_id"] = user_id
    if status:
        query["status"] = status
    
    if start_date or end_date:
        query["date"] = {}
        if start_date:
            query["date"]["$gte"] = start_date
        if end_date:
            query["date"]["$lte"] = end_date
    
    # Get total count
    total = await db.time_entries.count_documents(query)
    
    # Get entries with user info
    pipeline = [
        {"$match": query},
        {"$sort": {"date": -1, "created_at": -1}},
        {"$skip": (page - 1) * page_size},
        {"$limit": page_size},
        {
            "$lookup": {
                "from": "users",
                "localField": "user_id",
                "foreignField": "id",
                "as": "user"
            }
        },
        {"$unwind": {"path": "$user", "preserveNullAndEmptyArrays": True}},
        {
            "$project": {
                "_id": 0,
                "id": 1,
                "user_id": 1,
                "user_name": {"$concat": [
                    {"$ifNull": ["$user.first_name", ""]},
                    " ",
                    {"$ifNull": ["$user.last_name", ""]}
                ]},
                "employee_id": "$user.employee_id",
                "branch_id": 1,
                "team_id": 1,
                "job_site_id": 1,
                "date": 1,
                "clock_in": 1,
                "clock_out": 1,
                "total_hours": 1,
                "regular_hours": 1,
                "overtime_hours": 1,
                "break_minutes": 1,
                "status": 1,
                "flags": 1,
                "is_manual_entry": 1,
                "approval": 1,
                "created_at": 1,
                "updated_at": 1
            }
        }
    ]
    
    entries = await db.time_entries.aggregate(pipeline).to_list(page_size)
    
    return {
        "entries": entries,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }


@router.get("/{entry_id}")
async def get_time_entry(
    entry_id: str,
    current_user: TokenData = Depends(get_current_user)
):
    """Get single time entry details."""
    db = get_database()
    
    entry = await db.time_entries.find_one({"id": entry_id}, {"_id": 0})
    if not entry:
        raise NotFoundException("Time entry", entry_id)
    
    # Check access
    scope = get_role_data_scope(current_user.role)
    if scope == DataScope.BRANCH and entry.get("branch_id") != current_user.branch_id:
        raise ForbiddenException("Cannot access this entry")
    if scope == DataScope.TEAM and entry.get("team_id") != current_user.team_id:
        raise ForbiddenException("Cannot access this entry")
    if scope == DataScope.SELF and entry.get("user_id") != current_user.user_id:
        raise ForbiddenException("Cannot access this entry")
    
    # Get user info
    user = await db.users.find_one(
        {"id": entry["user_id"]},
        {"_id": 0, "id": 1, "first_name": 1, "last_name": 1, "employee_id": 1}
    )
    
    return {
        "entry": entry,
        "user": user
    }


@router.put("/{entry_id}")
async def edit_time_entry(
    entry_id: str,
    edit_data: TimeEntryEdit,
    req: Request,
    current_user: TokenData = Depends(get_current_user)
):
    """Edit a time entry (with audit trail)."""
    db = get_database()
    
    if not has_permission(current_user.role, "time_entries.override"):
        raise ForbiddenException("Cannot edit time entries")
    
    # Get existing entry
    entry = await db.time_entries.find_one({"id": entry_id}, {"_id": 0})
    if not entry:
        raise NotFoundException("Time entry", entry_id)
    
    # Check scope
    scope = get_role_data_scope(current_user.role)
    if scope == DataScope.BRANCH and entry.get("branch_id") != current_user.branch_id:
        raise ForbiddenException("Cannot edit this entry")
    
    now = utc_now()
    
    # Store original values for audit
    original_values = {
        "clock_in": entry.get("clock_in"),
        "clock_out": entry.get("clock_out"),
        "break_minutes": entry.get("break_minutes"),
        "total_hours": entry.get("total_hours")
    }
    
    # Prepare updates
    updates = {
        "updated_at": now.isoformat(),
        "edited_by": current_user.user_id,
        "edited_at": now.isoformat(),
        "edit_reason": edit_data.reason,
        "is_manual_entry": True
    }
    
    # Store original if first edit
    if not entry.get("original_values"):
        updates["original_values"] = original_values
    
    # Update clock in time
    if edit_data.clock_in_time:
        new_clock_in = entry.get("clock_in", {}).copy() if entry.get("clock_in") else {}
        new_clock_in["timestamp"] = edit_data.clock_in_time
        new_clock_in["local_time"] = edit_data.clock_in_time
        updates["clock_in"] = new_clock_in
    
    # Update clock out time
    if edit_data.clock_out_time:
        new_clock_out = entry.get("clock_out", {}).copy() if entry.get("clock_out") else {}
        new_clock_out["timestamp"] = edit_data.clock_out_time
        new_clock_out["local_time"] = edit_data.clock_out_time
        updates["clock_out"] = new_clock_out
    
    # Update break minutes
    if edit_data.break_minutes is not None:
        updates["break_minutes"] = edit_data.break_minutes
    
    # Update job site
    if edit_data.job_site_id:
        updates["job_site_id"] = edit_data.job_site_id
    
    # Recalculate hours if times changed
    clock_in = updates.get("clock_in", entry.get("clock_in"))
    clock_out = updates.get("clock_out", entry.get("clock_out"))
    break_mins = updates.get("break_minutes", entry.get("break_minutes", 0))
    
    if clock_in and clock_out:
        try:
            cin = datetime.fromisoformat(clock_in["timestamp"].replace("Z", "+00:00"))
            cout = datetime.fromisoformat(clock_out["timestamp"].replace("Z", "+00:00"))
            total_hours = (cout - cin).total_seconds() / 3600 - break_mins / 60
            total_hours = max(0, total_hours)
            updates["total_hours"] = round(total_hours, 2)
            updates["regular_hours"] = round(min(total_hours, 8.0), 2)
            updates["overtime_hours"] = round(max(0, total_hours - 8.0), 2)
            updates["status"] = "completed"
        except Exception as e:
            pass
    
    # Update entry
    await db.time_entries.update_one(
        {"id": entry_id},
        {"$set": updates}
    )
    
    # Create audit log
    await audit_log(
        db=db,
        actor_id=current_user.user_id,
        actor_email=current_user.email,
        actor_role=current_user.role,
        action="time_entry.override",
        target_type="time_entry",
        target_id=entry_id,
        target_ref=f"{entry.get('user_id')} - {entry.get('date')}",
        branch_id=entry.get("branch_id"),
        changes={
            "before": original_values,
            "after": {
                "clock_in": updates.get("clock_in"),
                "clock_out": updates.get("clock_out"),
                "break_minutes": updates.get("break_minutes"),
                "total_hours": updates.get("total_hours")
            }
        },
        metadata={"reason": edit_data.reason},
        request=req
    )
    
    # Get updated entry
    updated = await db.time_entries.find_one({"id": entry_id}, {"_id": 0})
    
    return {
        "message": "Time entry updated",
        "entry": updated
    }


@router.post("/{entry_id}/approve")
async def approve_time_entry(
    entry_id: str,
    approval: ApprovalAction,
    req: Request,
    current_user: TokenData = Depends(get_current_user)
):
    """Approve or reject a time entry."""
    db = get_database()
    
    if not has_permission(current_user.role, "time_entries.approve"):
        raise ForbiddenException("Cannot approve time entries")
    
    entry = await db.time_entries.find_one({"id": entry_id}, {"_id": 0})
    if not entry:
        raise NotFoundException("Time entry", entry_id)
    
    # Check scope
    scope = get_role_data_scope(current_user.role)
    if scope == DataScope.BRANCH and entry.get("branch_id") != current_user.branch_id:
        raise ForbiddenException("Cannot approve this entry")
    
    now = utc_now()
    
    if approval.action == "approve":
        new_status = "approved"
        action_name = "time_entry.approve"
    elif approval.action == "reject":
        new_status = "rejected"
        action_name = "time_entry.reject"
    else:
        raise BadRequestException("Invalid action. Use 'approve' or 'reject'")
    
    # Update entry
    await db.time_entries.update_one(
        {"id": entry_id},
        {
            "$set": {
                "status": new_status,
                "approval.required": True,
                "approval.approved_by": current_user.user_id,
                "approval.approved_at": now.isoformat(),
                "approval.notes": approval.notes,
                "updated_at": now.isoformat()
            }
        }
    )
    
    # Audit log
    await audit_log(
        db=db,
        actor_id=current_user.user_id,
        actor_email=current_user.email,
        actor_role=current_user.role,
        action=action_name,
        target_type="time_entry",
        target_id=entry_id,
        branch_id=entry.get("branch_id"),
        metadata={"notes": approval.notes},
        request=req
    )
    
    return {"message": f"Time entry {approval.action}d", "status": new_status}


@router.post("/bulk-approve")
async def bulk_approve_entries(
    bulk: BulkApproval,
    req: Request,
    current_user: TokenData = Depends(get_current_user)
):
    """Bulk approve or reject multiple time entries."""
    db = get_database()
    
    if not has_permission(current_user.role, "time_entries.approve"):
        raise ForbiddenException("Cannot approve time entries")
    
    if bulk.action not in ["approve", "reject"]:
        raise BadRequestException("Invalid action")
    
    now = utc_now()
    new_status = "approved" if bulk.action == "approve" else "rejected"
    action_name = f"time_entry.{bulk.action}"
    
    # Build scope filter
    scope = get_role_data_scope(current_user.role)
    scope_filter = {}
    if scope == DataScope.BRANCH:
        scope_filter["branch_id"] = current_user.branch_id
    elif scope == DataScope.TEAM:
        scope_filter["team_id"] = current_user.team_id
    
    # Update entries
    result = await db.time_entries.update_many(
        {
            "id": {"$in": bulk.entry_ids},
            **scope_filter
        },
        {
            "$set": {
                "status": new_status,
                "approval.required": True,
                "approval.approved_by": current_user.user_id,
                "approval.approved_at": now.isoformat(),
                "approval.notes": bulk.notes,
                "updated_at": now.isoformat()
            }
        }
    )
    
    # Audit log for bulk action
    await audit_log(
        db=db,
        actor_id=current_user.user_id,
        actor_email=current_user.email,
        actor_role=current_user.role,
        action=action_name,
        target_type="time_entry",
        target_id="bulk",
        metadata={
            "entry_ids": bulk.entry_ids,
            "count": result.modified_count,
            "notes": bulk.notes
        },
        request=req
    )
    
    return {
        "message": f"{result.modified_count} entries {bulk.action}d",
        "modified_count": result.modified_count
    }


@router.get("/pending-approval")
async def get_pending_approvals(
    branch_id: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: TokenData = Depends(get_current_user)
):
    """Get time entries pending approval."""
    db = get_database()
    
    if not has_permission(current_user.role, "time_entries.approve"):
        raise ForbiddenException("Cannot view pending approvals")
    
    scope = get_role_data_scope(current_user.role)
    
    query = {"status": "completed"}
    
    if scope == DataScope.BRANCH:
        query["branch_id"] = current_user.branch_id
    elif scope == DataScope.TEAM:
        query["team_id"] = current_user.team_id
    elif branch_id and scope == DataScope.ALL:
        query["branch_id"] = branch_id
    
    total = await db.time_entries.count_documents(query)
    
    pipeline = [
        {"$match": query},
        {"$sort": {"date": -1}},
        {"$skip": (page - 1) * page_size},
        {"$limit": page_size},
        {
            "$lookup": {
                "from": "users",
                "localField": "user_id",
                "foreignField": "id",
                "as": "user"
            }
        },
        {"$unwind": {"path": "$user", "preserveNullAndEmptyArrays": True}},
        {
            "$project": {
                "_id": 0,
                "id": 1,
                "user_id": 1,
                "user_name": {"$concat": ["$user.first_name", " ", "$user.last_name"]},
                "employee_id": "$user.employee_id",
                "date": 1,
                "clock_in": 1,
                "clock_out": 1,
                "total_hours": 1,
                "overtime_hours": 1,
                "flags": 1,
                "is_manual_entry": 1
            }
        }
    ]
    
    entries = await db.time_entries.aggregate(pipeline).to_list(page_size)
    
    return {
        "entries": entries,
        "total": total,
        "page": page,
        "page_size": page_size
    }
