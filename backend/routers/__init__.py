"""
Routers module initialization.
"""
from routers.auth import router as auth_router
from routers.attendance import router as attendance_router
from routers.gps import router as gps_router

__all__ = [
    "auth_router",
    "attendance_router",
    "gps_router"
]
