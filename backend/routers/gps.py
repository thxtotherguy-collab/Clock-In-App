"""
GPS tracking router - Real-time location logging.
"""
from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timezone
from typing import List

from core.database import get_database
from core.security import get_current_user, TokenData
from models.gps import GPSLogCreate, GPSBatchCreate, GPSLogResponse, GeoJSONPoint
from models.base import generate_uuid, utc_now
from utils.geo import haversine_distance

router = APIRouter(prefix="/gps", tags=["GPS Tracking"])


@router.post("/log", response_model=GPSLogResponse)
async def log_gps_position(
    request: GPSLogCreate,
    current_user: TokenData = Depends(get_current_user)
):
    """Log a single GPS position during active shift."""
    db = get_database()
    now = utc_now()
    
    # Get active time entry
    active_entry = await db.time_entries.find_one({
        "user_id": current_user.user_id,
        "clock_out": None,
        "status": "pending"
    }, {"_id": 0, "id": 1, "branch_id": 1, "job_site_id": 1})
    
    time_entry_id = active_entry["id"] if active_entry else None
    branch_id = active_entry.get("branch_id") if active_entry else current_user.branch_id
    
    # Check geofence
    is_within_geofence = True
    distance_from_site = None
    nearest_job_site_id = None
    
    if branch_id:
        branch = await db.branches.find_one(
            {"id": branch_id},
            {"_id": 0, "geofence": 1}
        )
        if branch and branch.get("geofence"):
            gf = branch["geofence"]
            center = gf.get("center", {})
            distance_from_site = haversine_distance(
                request.latitude, request.longitude,
                center.get("latitude", 0), center.get("longitude", 0)
            )
            is_within_geofence = distance_from_site <= gf.get("radius_meters", 150)
    
    # Create GPS log
    log = {
        "id": generate_uuid(),
        "user_id": current_user.user_id,
        "time_entry_id": time_entry_id,
        "branch_id": branch_id,
        "location": {
            "type": "Point",
            "coordinates": [request.longitude, request.latitude]
        },
        "accuracy_meters": request.accuracy_meters,
        "altitude_meters": request.altitude_meters,
        "speed_mps": request.speed_mps,
        "heading": request.heading,
        "captured_at": request.captured_at.isoformat(),
        "received_at": now.isoformat(),
        "is_within_geofence": is_within_geofence,
        "nearest_job_site_id": nearest_job_site_id,
        "distance_from_site_meters": distance_from_site,
        "battery_level": request.battery_level,
        "is_charging": request.is_charging,
        "is_offline_captured": request.is_offline_captured,
        "synced_at": now.isoformat() if request.is_offline_captured else None,
        "created_at": now.isoformat()
    }
    
    await db.gps_logs.insert_one(log)
    
    return GPSLogResponse(
        id=log["id"],
        user_id=log["user_id"],
        time_entry_id=time_entry_id,
        latitude=request.latitude,
        longitude=request.longitude,
        accuracy_meters=request.accuracy_meters,
        captured_at=request.captured_at,
        is_within_geofence=is_within_geofence,
        distance_from_site_meters=distance_from_site
    )


@router.post("/batch")
async def batch_upload_gps(
    request: GPSBatchCreate,
    current_user: TokenData = Depends(get_current_user)
):
    """Batch upload GPS logs (for offline sync)."""
    db = get_database()
    now = utc_now()
    
    # Get active or recent time entry
    active_entry = await db.time_entries.find_one({
        "user_id": current_user.user_id,
        "clock_out": None
    }, {"_id": 0, "id": 1, "branch_id": 1})
    
    time_entry_id = active_entry["id"] if active_entry else None
    branch_id = active_entry.get("branch_id") if active_entry else current_user.branch_id
    
    logs_to_insert = []
    for log_data in request.logs:
        log = {
            "id": generate_uuid(),
            "user_id": current_user.user_id,
            "time_entry_id": time_entry_id,
            "branch_id": branch_id,
            "location": {
                "type": "Point",
                "coordinates": [log_data.longitude, log_data.latitude]
            },
            "accuracy_meters": log_data.accuracy_meters,
            "altitude_meters": log_data.altitude_meters,
            "speed_mps": log_data.speed_mps,
            "heading": log_data.heading,
            "captured_at": log_data.captured_at.isoformat(),
            "received_at": now.isoformat(),
            "is_within_geofence": True,  # Will be validated later
            "battery_level": log_data.battery_level,
            "is_charging": log_data.is_charging,
            "is_offline_captured": log_data.is_offline_captured,
            "synced_at": now.isoformat(),
            "created_at": now.isoformat()
        }
        logs_to_insert.append(log)
    
    if logs_to_insert:
        await db.gps_logs.insert_many(logs_to_insert)
    
    return {
        "uploaded": len(logs_to_insert),
        "time_entry_id": time_entry_id
    }
