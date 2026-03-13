"""Production Health Check & Monitoring Endpoints.
Kubernetes-compatible liveness, readiness, and deep health probes.
"""
from fastapi import APIRouter
from datetime import datetime, timezone
import time
import os
import logging

from core.database import get_database

logger = logging.getLogger("health")
router = APIRouter(tags=["Health & Monitoring"])

# Track startup time
_start_time = time.time()


@router.get("/health")
async def health_check():
    """Basic liveness probe - quick response."""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": round(time.time() - _start_time, 1)
    }


@router.get("/health/ready")
async def readiness_check():
    """Readiness probe - checks all critical dependencies."""
    checks = {}
    overall_healthy = True

    # Database check
    try:
        db = get_database()
        start = time.time()
        await db.command("ping")
        db_latency = round((time.time() - start) * 1000, 1)
        checks["database"] = {
            "status": "connected",
            "latency_ms": db_latency
        }
        if db_latency > 5000:  # 5s is too slow
            checks["database"]["status"] = "degraded"
    except Exception as e:
        checks["database"] = {"status": "disconnected", "error": str(e)}
        overall_healthy = False

    # Scheduler check
    try:
        from services.scheduler_service import get_scheduler
        scheduler = get_scheduler()
        if scheduler and scheduler.running:
            checks["scheduler"] = {"status": "running", "jobs": len(scheduler.get_jobs())}
        else:
            checks["scheduler"] = {"status": "stopped"}
    except Exception:
        checks["scheduler"] = {"status": "unknown"}

    return {
        "status": "ready" if overall_healthy else "not_ready",
        "checks": checks,
        "uptime_seconds": round(time.time() - _start_time, 1),
        "version": "1.0.0"
    }


@router.get("/health/deep")
async def deep_health_check():
    """Deep health check - comprehensive system status for monitoring dashboards."""
    db = get_database()
    checks = {}

    # Database connectivity + stats
    try:
        start = time.time()
        await db.command("ping")
        db_latency = round((time.time() - start) * 1000, 1)

        # Collection counts
        user_count = await db.users.count_documents({"status": "active"})
        branch_count = await db.branches.count_documents({"status": "active"})
        entry_count = await db.time_entries.count_documents({})

        checks["database"] = {
            "status": "connected",
            "latency_ms": db_latency,
            "stats": {
                "active_users": user_count,
                "active_branches": branch_count,
                "total_time_entries": entry_count
            }
        }
    except Exception as e:
        checks["database"] = {"status": "error", "error": str(e)}

    # Memory usage
    try:
        import resource
        mem_usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024  # MB
        checks["memory"] = {"usage_mb": round(mem_usage, 1)}
    except Exception:
        checks["memory"] = {"status": "unknown"}

    # Scheduler
    try:
        from services.scheduler_service import get_scheduler
        scheduler = get_scheduler()
        if scheduler and scheduler.running:
            jobs = []
            for job in scheduler.get_jobs():
                jobs.append({
                    "id": job.id,
                    "name": job.name,
                    "next_run": job.next_run_time.isoformat() if job.next_run_time else None
                })
            checks["scheduler"] = {"status": "running", "jobs": jobs}
        else:
            checks["scheduler"] = {"status": "stopped"}
    except Exception:
        checks["scheduler"] = {"status": "unknown"}

    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": round(time.time() - _start_time, 1),
        "version": "1.0.0",
        "environment": os.environ.get("APP_ENV", "production"),
        "checks": checks
    }
