"""
Workforce Management System - Main Server
FastAPI application entry point.
Production-hardened with security middleware, monitoring, and GZip compression.
"""
from fastapi import FastAPI, APIRouter
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
import os
import logging
from pathlib import Path
from contextlib import asynccontextmanager

# Load environment
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

from core.database import connect_to_mongo, close_mongo_connection, get_database
from core.config import get_settings
from routers import auth_router, attendance_router, gps_router
from routers.admin_dashboard import router as admin_dashboard_router
from routers.admin_time_entries import router as admin_time_entries_router
from routers.admin_users import router as admin_users_router
from routers.admin_branches import router as admin_branches_router
from routers.exports import router as exports_router
from routers.admin_audit import router as admin_audit_router
from routers.reports import router as reports_router
from routers.health import router as health_router
from middleware.security import (
    SecurityHeadersMiddleware,
    RequestTrackingMiddleware,
    LoginRateLimitMiddleware
)

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

    # Initialize scheduler
    try:
        from services.scheduler_service import init_scheduler, shutdown_scheduler
        db = get_database()
        await init_scheduler(db)
        logger.info("Scheduler initialized")
    except Exception as e:
        logger.warning(f"Scheduler init failed (non-critical): {e}")

    yield

    # Shutdown
    try:
        from services.scheduler_service import shutdown_scheduler
        shutdown_scheduler()
    except Exception:
        pass
    await close_mongo_connection()
    logger.info("Database connection closed")


# Create the main app
app = FastAPI(
    title="Workforce Management System",
    description="Production-ready workforce management with GPS tracking, attendance, and payroll export",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs" if os.environ.get("APP_ENV") != "production" else None,
    redoc_url="/api/redoc" if os.environ.get("APP_ENV") != "production" else None
)

# Create API router
api_router = APIRouter(prefix="/api")


# Root endpoint
@api_router.get("/")
async def root():
    return {
        "message": "Workforce Management System API",
        "version": "1.0.0",
        "status": "operational"
    }


# Include routers
app.include_router(api_router)
app.include_router(health_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(attendance_router, prefix="/api")
app.include_router(gps_router, prefix="/api")
app.include_router(admin_dashboard_router, prefix="/api")
app.include_router(admin_time_entries_router, prefix="/api")
app.include_router(admin_users_router, prefix="/api")
app.include_router(admin_branches_router, prefix="/api")
app.include_router(exports_router, prefix="/api")
app.include_router(admin_audit_router, prefix="/api")
app.include_router(reports_router, prefix="/api")

# ═══ Middleware Stack (order matters: last added = first executed) ═══

# 1. CORS (outermost - must process OPTIONS first)
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. GZip compression for responses > 500 bytes
app.add_middleware(GZipMiddleware, minimum_size=500)

# 3. Security headers
app.add_middleware(SecurityHeadersMiddleware)

# 4. Request tracking (ID + timing)
app.add_middleware(RequestTrackingMiddleware)

# 5. Login rate limiting
app.add_middleware(LoginRateLimitMiddleware)
