"""
Geospatial utilities for GPS and geofence operations.
"""
import math
from typing import Tuple, Optional
from models.branch import GeoPoint, Geofence


def haversine_distance(
    lat1: float, lon1: float,
    lat2: float, lon2: float
) -> float:
    """
    Calculate the great-circle distance between two points on Earth.
    Returns distance in meters.
    """
    R = 6371000  # Earth's radius in meters
    
    # Convert to radians
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    # Haversine formula
    a = (
        math.sin(delta_lat / 2) ** 2 +
        math.cos(lat1_rad) * math.cos(lat2_rad) *
        math.sin(delta_lon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c


def is_within_geofence(
    point_lat: float,
    point_lon: float,
    geofence: Geofence
) -> Tuple[bool, float]:
    """
    Check if a point is within a circular geofence.
    Returns (is_within, distance_from_center).
    """
    distance = haversine_distance(
        point_lat, point_lon,
        geofence.center.latitude, geofence.center.longitude
    )
    
    return distance <= geofence.radius_meters, distance


def find_nearest_location(
    point_lat: float,
    point_lon: float,
    locations: list  # List of dicts with 'id', 'geofence' keys
) -> Tuple[Optional[str], Optional[float]]:
    """
    Find the nearest location from a list.
    Returns (location_id, distance_meters).
    """
    if not locations:
        return None, None
    
    nearest_id = None
    nearest_distance = float('inf')
    
    for loc in locations:
        if not loc.get('geofence'):
            continue
        
        geofence = loc['geofence']
        center = geofence.get('center', {})
        
        if not center:
            continue
        
        distance = haversine_distance(
            point_lat, point_lon,
            center.get('latitude', 0),
            center.get('longitude', 0)
        )
        
        if distance < nearest_distance:
            nearest_distance = distance
            nearest_id = loc.get('id')
    
    return nearest_id, nearest_distance if nearest_id else None


def validate_gps_accuracy(
    accuracy_meters: Optional[float],
    max_accuracy: float = 100
) -> bool:
    """
    Validate GPS accuracy is within acceptable range.
    Lower accuracy value = more accurate.
    """
    if accuracy_meters is None:
        return True  # Allow if not provided
    
    return accuracy_meters <= max_accuracy


def calculate_bounding_box(
    center_lat: float,
    center_lon: float,
    radius_meters: float
) -> dict:
    """
    Calculate a bounding box around a center point.
    Useful for efficient geospatial queries.
    """
    # Earth's radius in meters
    R = 6371000
    
    # Angular distance in radians
    angular_dist = radius_meters / R
    
    lat_rad = math.radians(center_lat)
    lon_rad = math.radians(center_lon)
    
    # Calculate bounds
    min_lat = math.degrees(lat_rad - angular_dist)
    max_lat = math.degrees(lat_rad + angular_dist)
    
    # Longitude adjustment for latitude
    delta_lon = math.asin(math.sin(angular_dist) / math.cos(lat_rad))
    min_lon = math.degrees(lon_rad - delta_lon)
    max_lon = math.degrees(lon_rad + delta_lon)
    
    return {
        "min_lat": min_lat,
        "max_lat": max_lat,
        "min_lon": min_lon,
        "max_lon": max_lon
    }
