"""
Attendance router - Clock in/out endpoints with GPS validation.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, Field
from datetime import datetime, timezone, date, timedelta
from typing import Optional, List

from core.database import get_database
from core.security import get_current_user, TokenData
from core.exceptions import BadRequestException, ConflictException, GeofenceException
from models.time_entry import (
    TimeEntry, ClockInRequest, ClockOutRequest, TimeEntryOverride,
    TimeEntryResponse, TodayStatusResponse, PunchMethod, TimeEntryStatus,
    GPSData, PunchData, OfflineSync, TimeEntryFlags
)
from models.base import generate_uuid, utc_now
from services.audit_service import audit_log
from utils.geo import haversine_distance, is_within_geofence

router = APIRouter(prefix="/attendance", tags=["Attendance"])


def calculate_hours(clock_in: datetime, clock_out: datetime, break_minutes: int = 0) -> float:
    """Calculate total hours between clock in and out."""
    delta = clock_out - clock_in
    hours = delta.total_seconds() / 3600
    hours -= break_minutes / 60
    return round(max(0, hours), 2)


async def validate_geofence(
    db, branch_id: str, job_site_id: Optional[str],
    latitude: float, longitude: float
) -> tuple:
    """Validate GPS coordinates against geofence. Returns (is_valid, distance, geofence_id)."""
    
    # Try job site geofence first
    if job_site_id:
        job_site = await db.job_sites.find_one(
            {"id": job_site_id},
            {"_id": 0, "geofence": 1}
        )
        if job_site and job_site.get("geofence"):
            gf = job_site["geofence"]
            center = gf.get("center", {})
            distance = haversine_distance(
                latitude, longitude,
                center.get("latitude", 0), center.get("longitude", 0)
            )
            is_within = distance <= gf.get("radius_meters", 150)
            return is_within, distance, job_site_id
    
    # Fall back to branch geofence
    if branch_id:
        branch = await db.branches.find_one(
            {"id": branch_id},
            {"_id": 0, "geofence": 1, "settings": 1}
        )
        if branch and branch.get("geofence"):
            gf = branch["geofence"]
            center = gf.get("center", {})
            distance = haversine_distance(
                latitude, longitude,
                center.get("latitude", 0), center.get("longitude", 0)
            )
            is_within = distance <= gf.get("radius_meters", 150)
            return is_within, distance, branch_id
    
    # No geofence configured - allow
    return True, 0, None


@router.post("/clock-in", response_model=TimeEntryResponse)
async def clock_in(
    request: ClockInRequest,
    req: Request,
    current_user: TokenData = Depends(get_current_user)
):
    """Clock in - start a new time entry."""
    db = get_database()
    now = utc_now()
    
    # DOUBLE CLOCK-IN PREVENTION
    # Check for existing active entry (clocked in but not out)
    active_entry = await db.time_entries.find_one({
        "user_id": current_user.user_id,
        "clock_out": None,
        "status": {"$in": ["pending", "completed"]}
    })
    
    if active_entry:
        raise ConflictException(
            "Already clocked in. Please clock out first before clocking in again."
        )
    
    # Get user's branch
    user = await db.users.find_one(
        {"id": current_user.user_id},
        {"_id": 0, "branch_id": 1, "team_id": 1}
    )
    branch_id = user.get("branch_id") if user else current_user.branch_id
    team_id = user.get("team_id") if user else current_user.team_id
    job_site_id = request.job_site_id
    
    # GPS validation
    within_geofence = True
    geofence_distance = None
    
    if request.gps:
        # Get branch settings
        branch = await db.branches.find_one(
            {"id": branch_id},
            {"_id": 0, "settings": 1}
        ) if branch_id else None
        
        require_gps = True
        if branch and branch.get("settings"):
            require_gps = branch["settings"].get("require_gps_for_punch", True)
        
        if require_gps:
            within_geofence, geofence_distance, _ = await validate_geofence(
                db, branch_id, job_site_id,
                request.gps.latitude, request.gps.longitude
            )
    
    # Determine timestamp (handle offline)
    punch_timestamp = now
    is_offline = False
    offline_id = None
    
    if request.offline_timestamp:
        punch_timestamp = request.offline_timestamp
        is_offline = True
        offline_id = request.offline_id
    
    # Build clock_in data
    clock_in_data = {
        "timestamp": punch_timestamp.isoformat(),
        "local_time": punch_timestamp.strftime("%Y-%m-%dT%H:%M:%S"),
        "gps": request.gps.model_dump() if request.gps else None,
        "photo_url": request.photo_url,
        "method": request.method.value,
        "device_info": request.device_info.model_dump() if request.device_info else None,
        "within_geofence": within_geofence,
        "geofence_distance_meters": geofence_distance
    }
    
    # Create time entry
    entry = {
        "id": generate_uuid(),
        "user_id": current_user.user_id,
        "branch_id": branch_id,
        "team_id": team_id,
        "job_site_id": job_site_id,
        "date": punch_timestamp.strftime("%Y-%m-%d"),
        "clock_in": clock_in_data,
        "clock_out": None,
        "total_hours": None,
        "regular_hours": None,
        "overtime_hours": None,
        "break_minutes": 0,
        "status": TimeEntryStatus.PENDING.value,
        "approval": {"required": False, "approved_by": None, "approved_at": None, "notes": None},
        "offline_sync": {
            "is_offline_entry": is_offline,
            "offline_id": offline_id,
            "synced_at": now.isoformat() if is_offline else None,
            "sync_conflicts": []
        },
        "is_manual_entry": False,
        "original_values": None,
        "edited_by": None,
        "edited_at": None,
        "edit_reason": None,
        "flags": {
            "late_clock_in": False,  # TODO: Check against shift
            "early_clock_out": False,
            "missing_clock_out": False,
            "outside_geofence": not within_geofence,
            "overtime_flagged": False
        },
        "created_at": now.isoformat(),
        "updated_at": now.isoformat()
    }
    
    await db.time_entries.insert_one(entry)
    
    # Audit log
    await audit_log(
        db=db,
        actor_id=current_user.user_id,
        actor_email=current_user.email,
        actor_role=current_user.role,
        action="time_entry.clock_in",
        target_type="time_entry",
        target_id=entry["id"],
        branch_id=branch_id,
        request=req
    )
    
    entry.pop("_id", None)
    return entry


@router.post("/clock-out", response_model=TimeEntryResponse)
async def clock_out(
    request: ClockOutRequest,
    req: Request,
    current_user: TokenData = Depends(get_current_user)
):
    """Clock out - complete the active time entry."""
    db = get_database()
    now = utc_now()
    
    # Find active entry
    active_entry = await db.time_entries.find_one({
        "user_id": current_user.user_id,
        "clock_out": None,
        "status": {"$in": ["pending"]}
    }, {"_id": 0})
    
    if not active_entry:
        raise BadRequestException("No active clock-in found. Please clock in first.")
    
    # GPS validation
    within_geofence = True
    geofence_distance = None
    
    if request.gps:
        within_geofence, geofence_distance, _ = await validate_geofence(
            db, active_entry.get("branch_id"), active_entry.get("job_site_id"),
            request.gps.latitude, request.gps.longitude
        )
    
    # Determine timestamp (handle offline)
    punch_timestamp = now
    is_offline = active_entry["offline_sync"]["is_offline_entry"]
    
    if request.offline_timestamp:
        punch_timestamp = request.offline_timestamp
        is_offline = True
    
    # Build clock_out data
    clock_out_data = {
        "timestamp": punch_timestamp.isoformat(),
        "local_time": punch_timestamp.strftime("%Y-%m-%dT%H:%M:%S"),
        "gps": request.gps.model_dump() if request.gps else None,
        "photo_url": request.photo_url,
        "method": request.method.value,
        "device_info": request.device_info.model_dump() if request.device_info else None,
        "within_geofence": within_geofence,
        "geofence_distance_meters": geofence_distance
    }
    
    # Calculate hours
    clock_in_time = datetime.fromisoformat(active_entry["clock_in"]["timestamp"].replace("Z", "+00:00"))
    total_hours = calculate_hours(clock_in_time, punch_timestamp, request.break_minutes)
    
    # Determine regular vs overtime (basic - using 8 hour threshold)
    regular_hours = min(total_hours, 8.0)
    overtime_hours = max(0, total_hours - 8.0)
    
    # Update entry
    update_data = {
        "clock_out": clock_out_data,
        "total_hours": total_hours,
        "regular_hours": regular_hours,
        "overtime_hours": overtime_hours,
        "break_minutes": request.break_minutes,
        "status": TimeEntryStatus.COMPLETED.value,
        "updated_at": now.isoformat(),
        "flags.overtime_flagged": overtime_hours > 0,
        "flags.outside_geofence": not within_geofence or active_entry["flags"]["outside_geofence"]
    }
    
    if is_offline:
        update_data["offline_sync.is_offline_entry"] = True
        update_data["offline_sync.synced_at"] = now.isoformat()
    
    await db.time_entries.update_one(
        {"id": active_entry["id"]},
        {"$set": update_data}
    )
    
    # Audit log
    await audit_log(
        db=db,
        actor_id=current_user.user_id,
        actor_email=current_user.email,
        actor_role=current_user.role,
        action="time_entry.clock_out",
        target_type="time_entry",
        target_id=active_entry["id"],
        branch_id=active_entry.get("branch_id"),
        request=req
    )
    
    # Get updated entry
    updated_entry = await db.time_entries.find_one(
        {"id": active_entry["id"]},
        {"_id": 0}
    )
    
    return updated_entry


@router.get("/today", response_model=TodayStatusResponse)
async def get_today_status(current_user: TokenData = Depends(get_current_user)):
    """Get today's attendance status for current user."""
    db = get_database()
    today = utc_now().strftime("%Y-%m-%d")
    
    # Check for active entry (clocked in but not out)
    active_entry = await db.time_entries.find_one({
        "user_id": current_user.user_id,
        "clock_out": None,
        "status": {"$in": ["pending"]}
    }, {"_id": 0})
    
    # Get all entries for today
    today_entries = await db.time_entries.find({
        "user_id": current_user.user_id,
        "date": today
    }, {"_id": 0}).to_list(100)
    
    # Calculate total hours today
    total_hours_today = sum(
        e.get("total_hours", 0) or 0 
        for e in today_entries 
        if e.get("total_hours")
    )
    
    return TodayStatusResponse(
        is_clocked_in=active_entry is not None,
        current_entry=active_entry,
        total_hours_today=round(total_hours_today, 2),
        entries_today=len(today_entries)
    )


@router.get("/week-summary")
async def get_week_summary(current_user: TokenData = Depends(get_current_user)):
    """Get week-to-date summary for current user."""
    db = get_database()
    now = utc_now()
    
    # Calculate week start (Monday)
    days_since_monday = now.weekday()
    week_start = (now - timedelta(days=days_since_monday)).strftime("%Y-%m-%d")
    today = now.strftime("%Y-%m-%d")
    
    # Get all entries for this week
    entries = await db.time_entries.find({
        "user_id": current_user.user_id,
        "date": {"$gte": week_start, "$lte": today},
        "status": {"$in": ["completed", "approved"]}
    }, {"_id": 0}).to_list(100)
    
    # Calculate totals
    total_hours = sum(e.get("total_hours", 0) or 0 for e in entries)
    regular_hours = sum(e.get("regular_hours", 0) or 0 for e in entries)
    overtime_hours = sum(e.get("overtime_hours", 0) or 0 for e in entries)
    
    # Group by day
    daily_breakdown = {}
    for entry in entries:
        day = entry["date"]
        if day not in daily_breakdown:
            daily_breakdown[day] = {"hours": 0, "entries": 0}
        daily_breakdown[day]["hours"] += entry.get("total_hours", 0) or 0
        daily_breakdown[day]["entries"] += 1
    
    return {
        "week_start": week_start,
        "week_end": today,
        "total_hours": round(total_hours, 2),
        "regular_hours": round(regular_hours, 2),
        "overtime_hours": round(overtime_hours, 2),
        "days_worked": len(daily_breakdown),
        "entries_count": len(entries),
        "daily_breakdown": daily_breakdown
    }


@router.get("/history")
async def get_attendance_history(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    current_user: TokenData = Depends(get_current_user)
):
    """Get attendance history for current user."""
    db = get_database()
    
    # Build query
    query = {"user_id": current_user.user_id}
    
    if start_date or end_date:
        query["date"] = {}
        if start_date:
            query["date"]["$gte"] = start_date
        if end_date:
            query["date"]["$lte"] = end_date
    
    # Get total count
    total = await db.time_entries.count_documents(query)
    
    # Get paginated results
    skip = (page - 1) * page_size
    entries = await db.time_entries.find(query, {"_id": 0}) \
        .sort("date", -1) \
        .skip(skip) \
        .limit(page_size) \
        .to_list(page_size)
    
    return {
        "entries": entries,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }


@router.post("/sync")
async def sync_offline_entries(
    entries: List[dict],
    current_user: TokenData = Depends(get_current_user)
):
    """Sync offline entries when connection restores."""
    db = get_database()
    now = utc_now()
    
    synced = []
    conflicts = []
    
    for entry_data in entries:
        offline_id = entry_data.get("offline_id")
        
        # Check if already synced
        existing = await db.time_entries.find_one({
            "offline_sync.offline_id": offline_id
        })
        
        if existing:
            conflicts.append({
                "offline_id": offline_id,
                "reason": "Already synced",
                "existing_id": existing["id"]
            })
            continue
        
        # Check for conflicts (same user, overlapping time)
        if entry_data.get("clock_in"):
            clock_in_time = entry_data["clock_in"].get("timestamp")
            entry_date = clock_in_time[:10] if clock_in_time else now.strftime("%Y-%m-%d")
            
            # Check for existing entry on same day
            day_entry = await db.time_entries.find_one({
                "user_id": current_user.user_id,
                "date": entry_date,
                "offline_sync.offline_id": {"$ne": offline_id}
            })
            
            if day_entry and not day_entry.get("clock_out"):
                conflicts.append({
                    "offline_id": offline_id,
                    "reason": "Active entry exists for this day",
                    "existing_id": day_entry["id"]
                })
                continue
        
        # Create entry
        entry = {
            "id": generate_uuid(),
            "user_id": current_user.user_id,
            "branch_id": entry_data.get("branch_id") or current_user.branch_id,
            "team_id": entry_data.get("team_id") or current_user.team_id,
            "job_site_id": entry_data.get("job_site_id"),
            "date": entry_data.get("date", now.strftime("%Y-%m-%d")),
            "clock_in": entry_data.get("clock_in"),
            "clock_out": entry_data.get("clock_out"),
            "total_hours": entry_data.get("total_hours"),
            "regular_hours": entry_data.get("regular_hours"),
            "overtime_hours": entry_data.get("overtime_hours"),
            "break_minutes": entry_data.get("break_minutes", 0),
            "status": entry_data.get("status", "completed"),
            "approval": {"required": False},
            "offline_sync": {
                "is_offline_entry": True,
                "offline_id": offline_id,
                "synced_at": now.isoformat(),
                "sync_conflicts": []
            },
            "flags": entry_data.get("flags", {}),
            "created_at": now.isoformat(),
            "updated_at": now.isoformat()
        }
        
        await db.time_entries.insert_one(entry)
        synced.append({"offline_id": offline_id, "server_id": entry["id"]})
    
    return {
        "synced": synced,
        "conflicts": conflicts,
        "synced_count": len(synced),
        "conflict_count": len(conflicts)
    }
