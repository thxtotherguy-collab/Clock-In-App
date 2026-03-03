"""
Database connection and utilities for MongoDB.
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
    """Initialize MongoDB connection."""
    logger.info("Connecting to MongoDB...")
    db_instance.client = AsyncIOMotorClient(mongo_url)
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
    """Create database indexes for optimal performance."""
    db = db_instance.db
    
    # Users indexes
    await db.users.create_index("email", unique=True)
    await db.users.create_index("employee_id", unique=True, sparse=True)
    await db.users.create_index([("branch_id", 1), ("status", 1)])
    await db.users.create_index([("role", 1), ("status", 1)])
    await db.users.create_index("team_id")
    
    # Branches indexes
    await db.branches.create_index("code", unique=True)
    await db.branches.create_index("status")
    
    # Teams indexes
    await db.teams.create_index("code", unique=True)
    await db.teams.create_index([("branch_id", 1), ("status", 1)])
    await db.teams.create_index("leader_id")
    
    # Job Sites indexes
    await db.job_sites.create_index("code", unique=True)
    await db.job_sites.create_index([("branch_id", 1), ("status", 1)])
    
    # Time Entries indexes
    await db.time_entries.create_index([("user_id", 1), ("date", -1)])
    await db.time_entries.create_index([("branch_id", 1), ("date", -1)])
    await db.time_entries.create_index([("team_id", 1), ("date", -1)])
    await db.time_entries.create_index([("job_site_id", 1), ("date", -1)])
    await db.time_entries.create_index([("status", 1), ("date", -1)])
    await db.time_entries.create_index("offline_sync.offline_id", sparse=True)
    
    # GPS Logs indexes
    await db.gps_logs.create_index([("user_id", 1), ("captured_at", -1)])
    await db.gps_logs.create_index("time_entry_id")
    
    # Overtime Records indexes
    await db.overtime_records.create_index([("user_id", 1), ("period_start", -1)])
    await db.overtime_records.create_index([("branch_id", 1), ("period_start", -1)])
    await db.overtime_records.create_index([("status", 1), ("period_start", -1)])
    
    # Audit Logs indexes
    await db.audit_logs.create_index([("actor_id", 1), ("timestamp", -1)])
    await db.audit_logs.create_index([("target_type", 1), ("target_id", 1), ("timestamp", -1)])
    await db.audit_logs.create_index([("action_category", 1), ("timestamp", -1)])
    await db.audit_logs.create_index([("branch_id", 1), ("timestamp", -1)])
    await db.audit_logs.create_index([("timestamp", -1)])
    
    # Rate Configurations indexes
    await db.rate_configurations.create_index("code", unique=True)
    await db.rate_configurations.create_index([("status", 1), ("effective_date", -1)])
    
    # Shifts indexes
    await db.shifts.create_index("code", unique=True)
    await db.shifts.create_index([("branch_id", 1), ("status", 1)])
    
    # Reports indexes
    await db.reports.create_index("created_by")
    await db.reports.create_index([("type", 1), ("scope.branch_id", 1)])
    
    logger.info("Database indexes created")


def get_database() -> AsyncIOMotorDatabase:
    """Get database instance for dependency injection."""
    return db_instance.db
