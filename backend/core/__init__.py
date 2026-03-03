"""
Core module initialization.
"""
from core.config import Settings, get_settings
from core.database import get_database, connect_to_mongo, close_mongo_connection
from core.security import (
    get_current_user,
    create_tokens,
    verify_password,
    get_password_hash,
    TokenData,
    TokenResponse
)
from core.exceptions import (
    AppException,
    NotFoundException,
    UnauthorizedException,
    ForbiddenException,
    BadRequestException,
    ConflictException,
    ValidationException,
    GeofenceException,
    OfflineSyncException
)

__all__ = [
    "Settings",
    "get_settings",
    "get_database",
    "connect_to_mongo",
    "close_mongo_connection",
    "get_current_user",
    "create_tokens",
    "verify_password",
    "get_password_hash",
    "TokenData",
    "TokenResponse",
    "AppException",
    "NotFoundException",
    "UnauthorizedException",
    "ForbiddenException",
    "BadRequestException",
    "ConflictException",
    "ValidationException",
    "GeofenceException",
    "OfflineSyncException"
]
