"""
Scheduler Service - APScheduler-based automation.
Triggers daily email reports at 6:00 PM (configurable per branch timezone).
"""
import logging
from datetime import datetime, timezone
from typing import Dict
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from motor.motor_asyncio import AsyncIOMotorDatabase

from services.report_generator import ReportGenerator
from services.email_service import EmailService
from models.base import generate_uuid, utc_now

logger = logging.getLogger("scheduler")

# Global scheduler instance
_scheduler: AsyncIOScheduler = None
_db = None


def get_scheduler() -> AsyncIOScheduler:
    """Get the global scheduler instance."""
    return _scheduler


async def init_scheduler(db: AsyncIOMotorDatabase):
    """Initialize and start the scheduler."""
    global _scheduler, _db
    _db = db

    _scheduler = AsyncIOScheduler(timezone="UTC")

    # Default daily report job at 18:00 UTC (can be configured per branch)
    _scheduler.add_job(
        run_daily_reports,
        CronTrigger(hour=18, minute=0),
        id="daily_report_1800",
        name="Daily Attendance Report (18:00 UTC)",
        replace_existing=True,
        misfire_grace_time=3600  # Allow 1 hour misfire
    )

    _scheduler.start()
    logger.info("[Scheduler] Started with daily report job at 18:00 UTC")

    # Log next run time
    job = _scheduler.get_job("daily_report_1800")
    if job:
        logger.info(f"[Scheduler] Next daily report: {job.next_run_time}")

    return _scheduler


def shutdown_scheduler():
    """Shutdown the scheduler."""
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=False)
        logger.info("[Scheduler] Shutdown complete")


async def run_daily_reports():
    """Execute daily report generation and distribution."""
    global _db
    if not _db:
        logger.error("[Scheduler] No database connection")
        return

    logger.info("[Scheduler] Starting daily report generation...")

    try:
        report_gen = ReportGenerator(_db)
        email_svc = EmailService(_db)

        # Get report config from DB
        config = await _db.report_configs.find_one(
            {"type": "daily_attendance", "enabled": True},
            {"_id": 0}
        )

        if not config:
            # Use default config
            config = {
                "type": "daily_attendance",
                "enabled": True,
                "send_per_branch": True,
                "global_recipients": [],
                "hr_cc": [],
                "finance_cc": [],
                "branch_recipients": {}
            }

        # Get active branches
        branches = await _db.branches.find(
            {"status": "active"},
            {"_id": 0}
        ).to_list(100)

        results = []

        if config.get("send_per_branch", True):
            # Send per-branch reports
            for branch in branches:
                try:
                    report_data = await report_gen.generate_daily_report(
                        branch_id=branch["id"]
                    )

                    # Determine recipients
                    recipients = list(set(
                        config.get("global_recipients", []) +
                        config.get("branch_recipients", {}).get(branch["id"], [])
                    ))

                    # Add branch admins
                    branch_admins = await _db.users.find(
                        {
                            "branch_id": branch["id"],
                            "role": {"$in": ["SUPER_ADMIN", "BRANCH_ADMIN"]},
                            "status": "active"
                        },
                        {"_id": 0, "email": 1}
                    ).to_list(50)
                    recipients.extend([a["email"] for a in branch_admins])
                    recipients = list(set(recipients))

                    if not recipients:
                        logger.warning(f"[Scheduler] No recipients for branch {branch['name']}")
                        continue

                    cc = list(set(
                        config.get("hr_cc", []) +
                        config.get("finance_cc", [])
                    ))

                    result = await email_svc.send_daily_report(
                        report_data=report_data,
                        recipients=recipients,
                        cc=cc,
                        branch_name=branch["name"]
                    )
                    results.append(result)
                    logger.info(f"[Scheduler] Report sent for branch: {branch['name']}")

                except Exception as e:
                    logger.error(f"[Scheduler] Error for branch {branch['name']}: {e}")
                    results.append({"branch": branch["name"], "status": "error", "error": str(e)})
        else:
            # Send one combined report
            try:
                report_data = await report_gen.generate_daily_report()
                recipients = config.get("global_recipients", [])
                cc = list(set(
                    config.get("hr_cc", []) +
                    config.get("finance_cc", [])
                ))

                if recipients:
                    result = await email_svc.send_daily_report(
                        report_data=report_data,
                        recipients=recipients,
                        cc=cc,
                        branch_name="All Branches"
                    )
                    results.append(result)
            except Exception as e:
                logger.error(f"[Scheduler] Error for combined report: {e}")

        # Log run result
        await _db.report_runs.insert_one({
            "id": generate_uuid(),
            "type": "daily_attendance",
            "trigger": "scheduled",
            "status": "completed",
            "results": results,
            "branches_processed": len(branches),
            "emails_sent": len([r for r in results if r.get("status") in ("sent", "mocked")]),
            "run_at": utc_now().isoformat()
        })

        logger.info(
            f"[Scheduler] Daily report complete: {len(results)} emails, "
            f"{len(branches)} branches"
        )

    except Exception as e:
        logger.error(f"[Scheduler] Daily report failed: {e}")
        await _db.report_runs.insert_one({
            "id": generate_uuid(),
            "type": "daily_attendance",
            "trigger": "scheduled",
            "status": "failed",
            "error": str(e),
            "run_at": utc_now().isoformat()
        })


async def trigger_manual_report(
    db: AsyncIOMotorDatabase,
    branch_id: str = None,
    triggered_by: str = None
) -> Dict:
    """Manually trigger a report send."""
    report_gen = ReportGenerator(db)
    email_svc = EmailService(db)

    # Get config
    config = await db.report_configs.find_one(
        {"type": "daily_attendance"},
        {"_id": 0}
    )
    if not config:
        config = {
            "global_recipients": [],
            "hr_cc": [],
            "finance_cc": [],
            "branch_recipients": {}
        }

    results = []

    if branch_id:
        # Single branch
        branch = await db.branches.find_one({"id": branch_id}, {"_id": 0})
        branch_name = branch["name"] if branch else "Unknown"

        report_data = await report_gen.generate_daily_report(branch_id=branch_id)

        recipients = list(set(
            config.get("global_recipients", []) +
            config.get("branch_recipients", {}).get(branch_id, [])
        ))

        # Add branch admins
        admins = await db.users.find(
            {"branch_id": branch_id, "role": {"$in": ["SUPER_ADMIN", "BRANCH_ADMIN"]}, "status": "active"},
            {"_id": 0, "email": 1}
        ).to_list(50)
        recipients.extend([a["email"] for a in admins])
        recipients = list(set(recipients))

        if not recipients:
            recipients = [triggered_by] if triggered_by else []

        cc = list(set(config.get("hr_cc", []) + config.get("finance_cc", [])))

        result = await email_svc.send_daily_report(
            report_data=report_data,
            recipients=recipients,
            cc=cc,
            branch_name=branch_name
        )
        results.append(result)
    else:
        # All branches
        branches = await db.branches.find({"status": "active"}, {"_id": 0}).to_list(100)

        for branch in branches:
            report_data = await report_gen.generate_daily_report(branch_id=branch["id"])

            recipients = list(set(
                config.get("global_recipients", []) +
                config.get("branch_recipients", {}).get(branch["id"], [])
            ))

            admins = await db.users.find(
                {"branch_id": branch["id"], "role": {"$in": ["SUPER_ADMIN", "BRANCH_ADMIN"]}, "status": "active"},
                {"_id": 0, "email": 1}
            ).to_list(50)
            recipients.extend([a["email"] for a in admins])
            recipients = list(set(recipients))

            if not recipients:
                recipients = [triggered_by] if triggered_by else []

            cc = list(set(config.get("hr_cc", []) + config.get("finance_cc", [])))

            result = await email_svc.send_daily_report(
                report_data=report_data,
                recipients=recipients,
                cc=cc,
                branch_name=branch["name"]
            )
            results.append(result)

    # Log run
    await db.report_runs.insert_one({
        "id": generate_uuid(),
        "type": "daily_attendance",
        "trigger": "manual",
        "triggered_by": triggered_by,
        "status": "completed",
        "results": results,
        "emails_sent": len(results),
        "run_at": utc_now().isoformat()
    })

    return {
        "status": "completed",
        "emails_sent": len(results),
        "results": results
    }
