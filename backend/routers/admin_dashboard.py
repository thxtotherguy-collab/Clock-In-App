"""
Admin Dashboard router - Real-time overview and statistics.
"""
from fastapi import APIRouter, Depends, Query
from datetime import datetime, timezone, timedelta
from typing import Optional, List

from core.database import get_database
from core.security import get_current_user, TokenData
from core.exceptions import ForbiddenException
from middleware.permissions import require_permission, DataScopeFilter
from models.role import has_permission, get_role_data_scope, DataScope

router = APIRouter(prefix="/admin/dashboard", tags=["Admin Dashboard"])


def get_date_range(date_str: Optional[str] = None):
    """Get start and end of a date."""
    if date_str:
        date = datetime.strptime(date_str, "%Y-%m-%d")
    else:
        date = datetime.now(timezone.utc)
    
    start = date.replace(hour=0, minute=0, second=0, microsecond=0)
    end = date.replace(hour=23, minute=59, second=59, microsecond=999999)
    return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")


@router.get("/overview")
async def get_dashboard_overview(
    branch_id: Optional[str] = None,
    date: Optional[str] = None,
    current_user: TokenData = Depends(get_current_user)
):
    """
    Get real-time dashboard overview.
    Returns: total_clocked_in, late_staff, absent_staff, total_hours_today
    """
    db = get_database()
    
    # Check permissions
    if not has_permission(current_user.role, "time_entries.view_branch"):
        if not has_permission(current_user.role, "time_entries.view_team"):
            raise ForbiddenException("Insufficient permissions for dashboard")
    
    # Determine data scope
    scope = get_role_data_scope(current_user.role)
    target_date, _ = get_date_range(date)
    
    # Build branch filter based on role
    branch_filter = {}
    if scope == DataScope.BRANCH:
        branch_filter["branch_id"] = current_user.branch_id
    elif scope == DataScope.TEAM:
        branch_filter["team_id"] = current_user.team_id
    elif branch_id and scope == DataScope.ALL:
        branch_filter["branch_id"] = branch_id
    
    # Get all workers in scope
    user_query = {"role": "WORKER", "status": "active", **branch_filter}
    total_workers = await db.users.count_documents(user_query)
    worker_ids = [u["id"] async for u in db.users.find(user_query, {"id": 1})]
    
    # Get today's time entries
    entry_query = {
        "date": target_date,
        "user_id": {"$in": worker_ids}
    }
    
    entries = await db.time_entries.find(entry_query, {"_id": 0}).to_list(1000)
    
    # Calculate metrics
    clocked_in_users = set()
    late_users = set()
    total_hours = 0
    
    for entry in entries:
        user_id = entry["user_id"]
        clocked_in_users.add(user_id)
        
        # Check if late (simplified - after 9 AM)
        if entry.get("clock_in"):
            clock_in_time = entry["clock_in"].get("timestamp", "")
            if clock_in_time:
                try:
                    cin = datetime.fromisoformat(clock_in_time.replace("Z", "+00:00"))
                    if cin.hour >= 9 and cin.minute > 15:
                        late_users.add(user_id)
                except:
                    pass
        
        # Sum hours
        if entry.get("total_hours"):
            total_hours += entry["total_hours"]
    
    # Calculate absent (workers who haven't clocked in)
    absent_count = total_workers - len(clocked_in_users)
    
    # Currently clocked in (no clock out yet)
    currently_clocked_in = await db.time_entries.count_documents({
        "date": target_date,
        "user_id": {"$in": worker_ids},
        "clock_out": None
    })
    
    return {
        "date": target_date,
        "total_workers": total_workers,
        "total_clocked_in": len(clocked_in_users),
        "currently_working": currently_clocked_in,
        "late_staff": len(late_users),
        "absent_staff": max(0, absent_count),
        "total_hours_today": round(total_hours, 2),
        "avg_hours_per_worker": round(total_hours / len(clocked_in_users), 2) if clocked_in_users else 0
    }


@router.get("/live-status")
async def get_live_status(
    branch_id: Optional[str] = None,
    current_user: TokenData = Depends(get_current_user)
):
    """Get live status of all workers (who's clocked in now)."""
    db = get_database()
    
    if not has_permission(current_user.role, "time_entries.view_branch"):
        raise ForbiddenException("Insufficient permissions")
    
    scope = get_role_data_scope(current_user.role)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    # Build filter
    branch_filter = {}
    if scope == DataScope.BRANCH:
        branch_filter["branch_id"] = current_user.branch_id
    elif branch_id and scope == DataScope.ALL:
        branch_filter["branch_id"] = branch_id
    
    # Get active entries (clocked in, not out)
    pipeline = [
        {
            "$match": {
                "date": today,
                "clock_out": None,
                **branch_filter
            }
        },
        {
            "$lookup": {
                "from": "users",
                "localField": "user_id",
                "foreignField": "id",
                "as": "user"
            }
        },
        {"$unwind": "$user"},
        {
            "$project": {
                "_id": 0,
                "entry_id": "$id",
                "user_id": 1,
                "user_name": {"$concat": ["$user.first_name", " ", "$user.last_name"]},
                "employee_id": "$user.employee_id",
                "clock_in_time": "$clock_in.timestamp",
                "branch_id": 1,
                "job_site_id": 1,
                "gps": "$clock_in.gps"
            }
        }
    ]
    
    active_workers = await db.time_entries.aggregate(pipeline).to_list(500)
    
    # Calculate elapsed time for each
    now = datetime.now(timezone.utc)
    for worker in active_workers:
        if worker.get("clock_in_time"):
            try:
                cin = datetime.fromisoformat(worker["clock_in_time"].replace("Z", "+00:00"))
                elapsed = now - cin
                worker["elapsed_hours"] = round(elapsed.total_seconds() / 3600, 2)
            except:
                worker["elapsed_hours"] = 0
    
    return {
        "count": len(active_workers),
        "workers": active_workers
    }


@router.get("/attendance-summary")
async def get_attendance_summary(
    branch_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: TokenData = Depends(get_current_user)
):
    """Get attendance summary for date range."""
    db = get_database()
    
    if not has_permission(current_user.role, "reports.view_branch"):
        raise ForbiddenException("Insufficient permissions")
    
    scope = get_role_data_scope(current_user.role)
    
    # Default to last 7 days
    if not end_date:
        end_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if not start_date:
        start = datetime.now(timezone.utc) - timedelta(days=7)
        start_date = start.strftime("%Y-%m-%d")
    
    # Build filter
    match_filter = {
        "date": {"$gte": start_date, "$lte": end_date}
    }
    
    if scope == DataScope.BRANCH:
        match_filter["branch_id"] = current_user.branch_id
    elif branch_id and scope == DataScope.ALL:
        match_filter["branch_id"] = branch_id
    
    # Aggregate by date
    pipeline = [
        {"$match": match_filter},
        {
            "$group": {
                "_id": "$date",
                "total_entries": {"$sum": 1},
                "total_hours": {"$sum": {"$ifNull": ["$total_hours", 0]}},
                "overtime_hours": {"$sum": {"$ifNull": ["$overtime_hours", 0]}},
                "unique_workers": {"$addToSet": "$user_id"}
            }
        },
        {
            "$project": {
                "_id": 0,
                "date": "$_id",
                "total_entries": 1,
                "total_hours": {"$round": ["$total_hours", 2]},
                "overtime_hours": {"$round": ["$overtime_hours", 2]},
                "workers_count": {"$size": "$unique_workers"}
            }
        },
        {"$sort": {"date": -1}}
    ]
    
    summary = await db.time_entries.aggregate(pipeline).to_list(100)
    
    # Calculate totals
    total_hours = sum(d.get("total_hours", 0) for d in summary)
    total_ot = sum(d.get("overtime_hours", 0) for d in summary)
    
    return {
        "start_date": start_date,
        "end_date": end_date,
        "daily_summary": summary,
        "totals": {
            "total_hours": round(total_hours, 2),
            "overtime_hours": round(total_ot, 2),
            "days_count": len(summary)
        }
    }


@router.get("/branch-comparison")
async def get_branch_comparison(
    date: Optional[str] = None,
    current_user: TokenData = Depends(get_current_user)
):
    """Compare performance across branches (Super Admin / Company Admin only)."""
    db = get_database()
    
    if not has_permission(current_user.role, "branches.view_all"):
        raise ForbiddenException("Only admins can view branch comparison")
    
    target_date = date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    # Get all branches
    branches = await db.branches.find(
        {"status": "active"},
        {"_id": 0, "id": 1, "name": 1, "code": 1}
    ).to_list(100)
    
    branch_stats = []
    for branch in branches:
        # Count workers in branch
        worker_count = await db.users.count_documents({
            "branch_id": branch["id"],
            "role": "WORKER",
            "status": "active"
        })
        
        # Get entries for branch
        entries = await db.time_entries.find({
            "branch_id": branch["id"],
            "date": target_date
        }, {"_id": 0}).to_list(500)
        
        clocked_in = len(set(e["user_id"] for e in entries))
        total_hours = sum(e.get("total_hours", 0) or 0 for e in entries)
        
        branch_stats.append({
            "branch_id": branch["id"],
            "branch_name": branch["name"],
            "branch_code": branch["code"],
            "total_workers": worker_count,
            "clocked_in": clocked_in,
            "absent": max(0, worker_count - clocked_in),
            "attendance_rate": round((clocked_in / worker_count * 100) if worker_count > 0 else 0, 1),
            "total_hours": round(total_hours, 2)
        })
    
    # Sort by attendance rate
    branch_stats.sort(key=lambda x: x["attendance_rate"], reverse=True)
    
    return {
        "date": target_date,
        "branches": branch_stats
    }
