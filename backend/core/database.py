"""
Database connection and utilities for MongoDB.
Production-hardened with comprehensive indexing for 300+ users.
"""
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class Database:
    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None


db_instance = Database()


async def connect_to_mongo(mongo_url: str, db_name: str):
    """Initialize MongoDB connection with production settings."""
    logger.info("Connecting to MongoDB...")
    db_instance.client = AsyncIOMotorClient(
        mongo_url,
        maxPoolSize=50,            # Connection pool for 300+ concurrent users
        minPoolSize=10,            # Keep warm connections
        maxIdleTimeMS=60000,       # Close idle connections after 60s
        serverSelectionTimeoutMS=5000,
        connectTimeoutMS=5000,
        retryWrites=True,
        retryReads=True
    )
    db_instance.db = db_instance.client[db_name]
    
    # Create indexes
    await create_indexes()
    logger.info("MongoDB connection established")


async def close_mongo_connection():
    """Close MongoDB connection."""
    if db_instance.client:
        db_instance.client.close()
        logger.info("MongoDB connection closed")


async def create_indexes():
    """Create database indexes for optimal performance at 300+ user scale."""
    db = db_instance.db
    
    # ═══ Users Collection ═══
    await db.users.create_index("email", unique=True)
    await db.users.create_index("employee_id", unique=True, sparse=True)
    await db.users.create_index("id", unique=True)
    await db.users.create_index([("branch_id", 1), ("status", 1)])
    await db.users.create_index([("role", 1), ("status", 1)])
    await db.users.create_index("team_id")
    await db.users.create_index([("branch_id", 1), ("role", 1), ("status", 1)])  # Admin dashboard queries
    await db.users.create_index([("status", 1), ("created_at", -1)])  # User list pagination
    
    # ═══ Branches Collection ═══
    await db.branches.create_index("id", unique=True)
    await db.branches.create_index("code", unique=True)
    await db.branches.create_index("status")
    
    # ═══ Teams Collection ═══
    await db.teams.create_index("id", unique=True)
    await db.teams.create_index("code", unique=True)
    await db.teams.create_index([("branch_id", 1), ("status", 1)])
    await db.teams.create_index("leader_id")
    
    # ═══ Job Sites Collection ═══
    await db.job_sites.create_index("id", unique=True)
    await db.job_sites.create_index("code", unique=True)
    await db.job_sites.create_index([("branch_id", 1), ("status", 1)])
    
    # ═══ Time Entries Collection (CRITICAL for performance) ═══
    await db.time_entries.create_index("id", unique=True)
    await db.time_entries.create_index([("user_id", 1), ("date", -1)])  # Worker's own history
    await db.time_entries.create_index([("branch_id", 1), ("date", -1)])  # Branch dashboard
    await db.time_entries.create_index([("team_id", 1), ("date", -1)])  # Team leader view
    await db.time_entries.create_index([("status", 1), ("date", -1)])  # Pending approvals
    await db.time_entries.create_index([("branch_id", 1), ("status", 1), ("date", -1)])  # Admin filtered
    await db.time_entries.create_index([("user_id", 1), ("date", 1), ("status", 1)])  # Clock-in check
    await db.time_entries.create_index("offline_sync.offline_id", sparse=True)  # Offline sync
    await db.time_entries.create_index([("date", -1), ("branch_id", 1)])  # Export queries
    
    # ═══ GPS Logs Collection ═══
    await db.gps_logs.create_index("id", unique=True)
    await db.gps_logs.create_index([("user_id", 1), ("captured_at", -1)])
    await db.gps_logs.create_index("time_entry_id")
    await db.gps_logs.create_index([("captured_at", -1)])
    # Geospatial index for location queries
    try:
        await db.gps_logs.create_index([("location.coordinates", "2dsphere")])
    except Exception:
        pass  # May fail if data format doesn't match
    
    # ═══ Overtime Records Collection ═══
    await db.overtime_records.create_index("id", unique=True)
    await db.overtime_records.create_index([("user_id", 1), ("period_start", -1)])
    await db.overtime_records.create_index([("branch_id", 1), ("period_start", -1)])
    await db.overtime_records.create_index([("status", 1), ("period_start", -1)])
    
    # ═══ Audit Logs Collection ═══
    await db.audit_logs.create_index("id", unique=True)
    await db.audit_logs.create_index([("actor_id", 1), ("timestamp", -1)])
    await db.audit_logs.create_index([("target_type", 1), ("target_id", 1), ("timestamp", -1)])
    await db.audit_logs.create_index([("action_category", 1), ("timestamp", -1)])
    await db.audit_logs.create_index([("branch_id", 1), ("timestamp", -1)])
    await db.audit_logs.create_index([("timestamp", -1)])
    await db.audit_logs.create_index([("action", 1), ("timestamp", -1)])
    
    # ═══ Rate Configurations Collection ═══
    await db.rate_configurations.create_index("id", unique=True)
    await db.rate_configurations.create_index("code", unique=True)
    await db.rate_configurations.create_index([("status", 1), ("effective_date", -1)])
    
    # ═══ Shifts Collection ═══
    await db.shifts.create_index("id", unique=True)
    await db.shifts.create_index("code", unique=True)
    await db.shifts.create_index([("branch_id", 1), ("status", 1)])
    
    # ═══ Reports Collection ═══
    await db.reports.create_index("id", unique=True)
    await db.reports.create_index("created_by")
    await db.reports.create_index([("type", 1), ("scope.branch_id", 1)])
    
    # ═══ Phase 5: Report Engine Collections ═══
    await db.report_configs.create_index("type", unique=True)
    await db.report_runs.create_index("id", unique=True)
    await db.report_runs.create_index([("run_at", -1)])
    await db.report_runs.create_index([("type", 1), ("run_at", -1)])
    await db.email_logs.create_index("id", unique=True)
    await db.email_logs.create_index([("sent_at", -1)])
    await db.email_logs.create_index([("report_type", 1), ("sent_at", -1)])
    
    # ═══ Phase 6: Security Collections ═══
    await db.login_attempts.create_index("id", unique=True)
    await db.login_attempts.create_index([("email", 1), ("timestamp", -1)])
    await db.login_attempts.create_index([("ip_address", 1), ("timestamp", -1)])
    # TTL index: auto-delete login attempts after 24 hours
    try:
        await db.login_attempts.create_index(
            "created_at_dt",
            expireAfterSeconds=86400  # 24 hours
        )
    except Exception:
        pass
    
    logger.info("Database indexes created (production-optimized)")


def get_database() -> AsyncIOMotorDatabase:
    """Get database instance for dependency injection."""
    return db_instance.db
