"""
GPS Tracking models and schemas.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

from models.base import BaseEntity


class GeoJSONPoint(BaseModel):
    """GeoJSON Point for MongoDB geospatial queries."""
    type: str = "Point"
    coordinates: List[float]  # [longitude, latitude]


# Database Model
class GPSLog(BaseEntity):
    """GPS tracking log database model."""
    user_id: str
    time_entry_id: Optional[str] = None
    branch_id: str
    
    # Location data (GeoJSON for MongoDB)
    location: GeoJSONPoint
    accuracy_meters: Optional[float] = None
    altitude_meters: Optional[float] = None
    speed_mps: Optional[float] = None  # Meters per second
    heading: Optional[float] = None  # Degrees
    
    # Timestamps
    captured_at: datetime
    received_at: datetime
    
    # Context
    is_within_geofence: bool = True
    nearest_job_site_id: Optional[str] = None
    distance_from_site_meters: Optional[float] = None
    
    # Device info
    battery_level: Optional[int] = None
    is_charging: Optional[bool] = None
    
    # Sync status
    is_offline_captured: bool = False
    synced_at: Optional[datetime] = None


# API Schemas
class GPSLogCreate(BaseModel):
    """Schema for creating a GPS log."""
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    accuracy_meters: Optional[float] = None
    altitude_meters: Optional[float] = None
    speed_mps: Optional[float] = None
    heading: Optional[float] = None
    captured_at: datetime
    battery_level: Optional[int] = Field(None, ge=0, le=100)
    is_charging: Optional[bool] = None
    is_offline_captured: bool = False


class GPSBatchCreate(BaseModel):
    """Schema for batch GPS log upload."""
    logs: List[GPSLogCreate]


class GPSLogResponse(BaseModel):
    """Schema for GPS log response."""
    id: str
    user_id: str
    time_entry_id: Optional[str] = None
    latitude: float
    longitude: float
    accuracy_meters: Optional[float] = None
    captured_at: datetime
    is_within_geofence: bool
    distance_from_site_meters: Optional[float] = None


class GPSTrackResponse(BaseModel):
    """Schema for GPS tracking data."""
    user_id: str
    logs: List[GPSLogResponse]
    total_points: int
    date_range: dict  # { start, end }


class LiveLocationResponse(BaseModel):
    """Schema for live location data."""
    user_id: str
    user_name: str
    latitude: float
    longitude: float
    accuracy_meters: Optional[float] = None
    captured_at: datetime
    is_within_geofence: bool
    battery_level: Optional[int] = None
