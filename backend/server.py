"""
Workforce Management System - Main Server
FastAPI application entry point.
"""
from fastapi import FastAPI, APIRouter
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
import os
import logging
from pathlib import Path
from contextlib import asynccontextmanager

# Load environment
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

from core.database import connect_to_mongo, close_mongo_connection, get_database
from core.config import get_settings

settings = get_settings()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown."""
    # Startup
    logger.info("Starting Workforce Management System...")
    await connect_to_mongo(settings.mongo_url, settings.db_name)
    logger.info("Database connected")
    yield
    # Shutdown
    await close_mongo_connection()
    logger.info("Database connection closed")


# Create the main app
app = FastAPI(
    title="Workforce Management System",
    description="Production-ready workforce management with GPS tracking, attendance, and payroll export",
    version="1.0.0",
    lifespan=lifespan
)

# Create API router
api_router = APIRouter(prefix="/api")


# Health check endpoint
@api_router.get("/")
async def root():
    return {
        "message": "Workforce Management System API",
        "version": "1.0.0",
        "status": "operational"
    }


@api_router.get("/health")
async def health_check():
    """Health check endpoint."""
    db = get_database()
    try:
        await db.command("ping")
        db_status = "connected"
    except Exception:
        db_status = "disconnected"
    
    return {
        "status": "healthy",
        "database": db_status,
        "version": "1.0.0"
    }


# Schema info endpoint (for documentation)
@api_router.get("/schema/roles")
async def get_roles_schema():
    """Get role definitions and permissions."""
    from models.role import ROLE_PERMISSIONS, ROLE_DATA_SCOPE, ROLE_LEVELS
    
    roles = []
    for role_name in ["SUPER_ADMIN", "BRANCH_ADMIN", "TEAM_LEADER", "WORKER"]:
        roles.append({
            "name": role_name,
            "level": ROLE_LEVELS.get(role_name, 0),
            "data_scope": ROLE_DATA_SCOPE.get(role_name, "self").value,
            "permissions": ROLE_PERMISSIONS.get(role_name, {})
        })
    
    return {"roles": roles}


@api_router.get("/schema/collections")
async def get_collections_schema():
    """Get database collection information."""
    return {
        "collections": [
            {
                "name": "users",
                "description": "All system users (admins, managers, workers)",
                "key_fields": ["id", "email", "employee_id", "role", "branch_id", "team_id"]
            },
            {
                "name": "branches",
                "description": "Branch/location configuration with geofence",
                "key_fields": ["id", "code", "name", "geofence", "settings"]
            },
            {
                "name": "teams",
                "description": "Teams within branches",
                "key_fields": ["id", "code", "branch_id", "leader_id"]
            },
            {
                "name": "job_sites",
                "description": "Job sites/work locations",
                "key_fields": ["id", "code", "branch_id", "geofence"]
            },
            {
                "name": "time_entries",
                "description": "Clock in/out records with GPS",
                "key_fields": ["id", "user_id", "date", "clock_in", "clock_out", "offline_sync"]
            },
            {
                "name": "gps_logs",
                "description": "Real-time GPS tracking during shifts",
                "key_fields": ["id", "user_id", "time_entry_id", "location", "captured_at"]
            },
            {
                "name": "overtime_records",
                "description": "Calculated overtime records",
                "key_fields": ["id", "user_id", "period_type", "overtime_hours", "rate_tier"]
            },
            {
                "name": "audit_logs",
                "description": "System audit trail",
                "key_fields": ["id", "actor_id", "action", "target_type", "target_id", "changes"]
            },
            {
                "name": "rate_configurations",
                "description": "Configurable overtime rate tiers",
                "key_fields": ["id", "code", "tiers", "branch_overrides"]
            },
            {
                "name": "shifts",
                "description": "Shift definitions",
                "key_fields": ["id", "code", "branch_id", "start_time", "end_time"]
            },
            {
                "name": "reports",
                "description": "Saved/scheduled report configurations",
                "key_fields": ["id", "type", "scope", "schedule", "output"]
            }
        ]
    }


# Include the router
app.include_router(api_router)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)
