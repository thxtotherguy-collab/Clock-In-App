"""
Reports & Automation Router.
- Report configuration (recipients, schedule)
- Manual report trigger (Send Report Now)
- Report preview
- Report run history
- SA BCEA overtime configuration
"""
from fastapi import APIRouter, Depends, Query
from datetime import datetime, date, timedelta, timezone
from typing import Optional, List
from pydantic import BaseModel, Field

from core.database import get_database
from core.security import get_current_user, TokenData
from core.exceptions import ForbiddenException, NotFoundException, BadRequestException
from models.role import has_permission, get_role_data_scope, DataScope
from models.base import generate_uuid, utc_now
from services.report_generator import ReportGenerator
from services.email_service import EmailService
from services.scheduler_service import trigger_manual_report, get_scheduler
from services.audit_service import audit_log

router = APIRouter(prefix="/reports", tags=["Reports & Automation"])


# ─── Pydantic Schemas ───

class ReportConfigUpdate(BaseModel):
    """Update report configuration."""
    enabled: Optional[bool] = None
    send_per_branch: Optional[bool] = None
    global_recipients: Optional[List[str]] = None
    hr_cc: Optional[List[str]] = None
    finance_cc: Optional[List[str]] = None
    branch_recipients: Optional[dict] = None
    schedule_hour: Optional[int] = Field(None, ge=0, le=23)
    schedule_minute: Optional[int] = Field(None, ge=0, le=59)


class SendNowRequest(BaseModel):
    """Manual report trigger request."""
    branch_id: Optional[str] = None
    report_date: Optional[str] = None


class OvertimeConfigUpdate(BaseModel):
    """Update SA BCEA overtime configuration."""
    name: Optional[str] = None
    daily_threshold_5day: Optional[float] = Field(None, ge=0, description="Daily OT threshold for 5-day week (SA BCEA: 9hrs)")
    daily_threshold_6day: Optional[float] = Field(None, ge=0, description="Daily OT threshold for 6-day week (SA BCEA: 8hrs)")
    weekly_threshold: Optional[float] = Field(None, ge=0, description="Weekly OT threshold (SA BCEA: 45hrs)")
    max_weekly_overtime: Optional[float] = Field(None, ge=0, description="Max weekly OT hours (SA BCEA: 10hrs)")
    standard_ot_multiplier: Optional[float] = Field(None, ge=1.0, description="Standard OT multiplier (SA BCEA: 1.5x)")
    sunday_multiplier: Optional[float] = Field(None, ge=1.0, description="Sunday rate multiplier (SA BCEA: 2.0x)")
    public_holiday_multiplier: Optional[float] = Field(None, ge=1.0, description="Public holiday multiplier (SA BCEA: 2.0x)")


# ─── Report Configuration ───

@router.get("/config")
async def get_report_config(
    current_user: TokenData = Depends(get_current_user)
):
    """Get the current report configuration."""
    if not has_permission(current_user.role, "reports.export"):
        raise ForbiddenException("Cannot access report config")

    db = get_database()

    config = await db.report_configs.find_one(
        {"type": "daily_attendance"},
        {"_id": 0}
    )

    if not config:
        # Create default config
        config = {
            "id": generate_uuid(),
            "type": "daily_attendance",
            "enabled": True,
            "send_per_branch": True,
            "global_recipients": [],
            "hr_cc": [],
            "finance_cc": [],
            "branch_recipients": {},
            "schedule_hour": 18,
            "schedule_minute": 0,
            "schedule_timezone": "UTC",
            "created_at": utc_now().isoformat(),
            "updated_at": utc_now().isoformat()
        }
        await db.report_configs.insert_one(config)
        config.pop("_id", None)

    return config


@router.put("/config")
async def update_report_config(
    update: ReportConfigUpdate,
    current_user: TokenData = Depends(get_current_user)
):
    """Update report configuration (recipients, schedule)."""
    if not has_permission(current_user.role, "reports.export"):
        raise ForbiddenException("Cannot modify report config")

    db = get_database()

    # Build update
    update_data = {k: v for k, v in update.model_dump().items() if v is not None}
    update_data["updated_at"] = utc_now().isoformat()

    # Upsert
    await db.report_configs.update_one(
        {"type": "daily_attendance"},
        {"$set": update_data},
        upsert=True
    )

    # Audit
    await audit_log(
        db=db,
        actor_id=current_user.user_id,
        actor_email=current_user.email,
        actor_role=current_user.role,
        action="report.config.update",
        target_type="report_config",
        target_id="daily_attendance",
        metadata=update_data
    )

    return {"message": "Report configuration updated", "updated_fields": list(update_data.keys())}


# ─── Manual Report Trigger ───

@router.post("/send-now")
async def send_report_now(
    request: SendNowRequest,
    current_user: TokenData = Depends(get_current_user)
):
    """Manually trigger sending the daily report now."""
    if not has_permission(current_user.role, "reports.export"):
        raise ForbiddenException("Cannot send reports")

    db = get_database()

    # Scope check for branch admins
    scope = get_role_data_scope(current_user.role)
    branch_id = request.branch_id

    if scope == DataScope.BRANCH:
        branch_id = current_user.branch_id  # Force own branch

    result = await trigger_manual_report(
        db=db,
        branch_id=branch_id,
        triggered_by=current_user.email
    )

    # Audit
    await audit_log(
        db=db,
        actor_id=current_user.user_id,
        actor_email=current_user.email,
        actor_role=current_user.role,
        action="report.send_manual",
        target_type="report",
        target_id="daily_attendance",
        metadata={
            "branch_id": branch_id,
            "emails_sent": result.get("emails_sent", 0)
        }
    )

    return result


# ─── Report Preview ───

@router.get("/preview")
async def preview_report(
    report_date: Optional[str] = None,
    branch_id: Optional[str] = None,
    current_user: TokenData = Depends(get_current_user)
):
    """Preview report content without sending."""
    if not has_permission(current_user.role, "reports.export"):
        raise ForbiddenException("Cannot preview reports")

    db = get_database()

    scope = get_role_data_scope(current_user.role)
    if scope == DataScope.BRANCH:
        branch_id = current_user.branch_id

    report_gen = ReportGenerator(db)
    report_data = await report_gen.generate_daily_report(
        report_date=report_date,
        branch_id=branch_id
    )

    return report_data


@router.get("/preview/html")
async def preview_report_html(
    report_date: Optional[str] = None,
    branch_id: Optional[str] = None,
    current_user: TokenData = Depends(get_current_user)
):
    """Preview the HTML email template."""
    if not has_permission(current_user.role, "reports.export"):
        raise ForbiddenException("Cannot preview reports")

    db = get_database()

    scope = get_role_data_scope(current_user.role)
    if scope == DataScope.BRANCH:
        branch_id = current_user.branch_id

    report_gen = ReportGenerator(db)
    report_data = await report_gen.generate_daily_report(
        report_date=report_date,
        branch_id=branch_id
    )

    email_svc = EmailService(db)

    # Get branch name
    branch_name = "All Branches"
    if branch_id:
        branch = await db.branches.find_one({"id": branch_id}, {"_id": 0, "name": 1})
        if branch:
            branch_name = branch["name"]

    html = email_svc._build_daily_report_html(report_data, branch_name)

    from fastapi.responses import HTMLResponse
    return HTMLResponse(content=html)


# ─── Report History ───

@router.get("/history")
async def get_report_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: TokenData = Depends(get_current_user)
):
    """Get history of sent reports."""
    if not has_permission(current_user.role, "reports.export"):
        raise ForbiddenException("Cannot view report history")

    db = get_database()

    total = await db.report_runs.count_documents({})
    skip = (page - 1) * page_size

    runs = await db.report_runs.find({}, {"_id": 0}) \
        .sort("run_at", -1) \
        .skip(skip) \
        .limit(page_size) \
        .to_list(page_size)

    return {
        "runs": runs,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/email-logs")
async def get_email_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    report_type: Optional[str] = None,
    current_user: TokenData = Depends(get_current_user)
):
    """Get email send logs."""
    if not has_permission(current_user.role, "reports.export"):
        raise ForbiddenException("Cannot view email logs")

    db = get_database()

    query = {}
    if report_type:
        query["report_type"] = report_type

    total = await db.email_logs.count_documents(query)
    skip = (page - 1) * page_size

    logs = await db.email_logs.find(query, {"_id": 0, "html_body": 0}) \
        .sort("sent_at", -1) \
        .skip(skip) \
        .limit(page_size) \
        .to_list(page_size)

    return {
        "logs": logs,
        "total": total,
        "page": page,
        "page_size": page_size
    }


# ─── Overtime Configuration (SA BCEA) ───

@router.get("/overtime-config")
async def get_overtime_config(
    current_user: TokenData = Depends(get_current_user)
):
    """Get the active overtime (SA BCEA) configuration."""
    if not has_permission(current_user.role, "reports.export"):
        raise ForbiddenException("Cannot access overtime config")

    db = get_database()

    config = await db.rate_configurations.find_one(
        {"status": "active"},
        {"_id": 0},
        sort=[("effective_date", -1)]
    )

    if not config:
        # Create default SA BCEA config
        now = utc_now()
        config = {
            "id": generate_uuid(),
            "name": "South African BCEA Standard",
            "code": "SA-BCEA-2025",
            "effective_date": date.today().isoformat(),
            "expiry_date": None,
            "status": "active",
            "description": "Basic Conditions of Employment Act - South Africa",
            "rules": {
                "daily_threshold_5day": 9.0,
                "daily_threshold_6day": 8.0,
                "weekly_threshold": 45.0,
                "max_weekly_overtime": 10.0,
                "max_daily_hours": 12.0
            },
            "tiers": {
                "standard": {
                    "description": "Regular hourly rate",
                    "multiplier": 1.0,
                    "applies_after_daily": 0,
                    "applies_after_weekly": 0
                },
                "standard_ot": {
                    "description": "Standard overtime (1.5x) - SA BCEA Section 10",
                    "multiplier": 1.5,
                    "applies_after_daily": 9.0,
                    "applies_after_weekly": 45.0
                },
                "sunday": {
                    "description": "Sunday work (2x) - SA BCEA Section 16",
                    "multiplier": 2.0
                },
                "public_holiday": {
                    "description": "Public holiday work (2x) - SA BCEA Section 18",
                    "multiplier": 2.0
                }
            },
            "branch_overrides": {},
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "created_by": "system"
        }
        await db.rate_configurations.insert_one(config)
        config.pop("_id", None)

    return config


@router.put("/overtime-config")
async def update_overtime_config(
    update: OvertimeConfigUpdate,
    current_user: TokenData = Depends(get_current_user)
):
    """Update overtime configuration."""
    if current_user.role != "SUPER_ADMIN":
        raise ForbiddenException("Only SUPER_ADMIN can modify overtime config")

    db = get_database()

    update_fields = {}
    data = update.model_dump(exclude_none=True)

    if "name" in data:
        update_fields["name"] = data["name"]
    if "daily_threshold_5day" in data:
        update_fields["rules.daily_threshold_5day"] = data["daily_threshold_5day"]
        update_fields["tiers.standard_ot.applies_after_daily"] = data["daily_threshold_5day"]
    if "daily_threshold_6day" in data:
        update_fields["rules.daily_threshold_6day"] = data["daily_threshold_6day"]
    if "weekly_threshold" in data:
        update_fields["rules.weekly_threshold"] = data["weekly_threshold"]
        update_fields["tiers.standard_ot.applies_after_weekly"] = data["weekly_threshold"]
    if "max_weekly_overtime" in data:
        update_fields["rules.max_weekly_overtime"] = data["max_weekly_overtime"]
    if "standard_ot_multiplier" in data:
        update_fields["tiers.standard_ot.multiplier"] = data["standard_ot_multiplier"]
    if "sunday_multiplier" in data:
        update_fields["tiers.sunday.multiplier"] = data["sunday_multiplier"]
    if "public_holiday_multiplier" in data:
        update_fields["tiers.public_holiday.multiplier"] = data["public_holiday_multiplier"]

    update_fields["updated_at"] = utc_now().isoformat()
    update_fields["updated_by"] = current_user.user_id

    result = await db.rate_configurations.update_one(
        {"status": "active"},
        {"$set": update_fields}
    )

    if result.matched_count == 0:
        raise NotFoundException("No active overtime configuration found")

    await audit_log(
        db=db,
        actor_id=current_user.user_id,
        actor_email=current_user.email,
        actor_role=current_user.role,
        action="overtime.config.update",
        target_type="rate_configuration",
        target_id="SA-BCEA",
        metadata=data
    )

    return {"message": "Overtime configuration updated", "updated_fields": list(data.keys())}


# ─── Payroll Summary ───

@router.get("/payroll-summary")
async def get_payroll_summary(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    branch_id: Optional[str] = None,
    current_user: TokenData = Depends(get_current_user)
):
    """Get payroll summary with SA BCEA overtime calculations."""
    if not has_permission(current_user.role, "reports.export"):
        raise ForbiddenException("Cannot access payroll data")

    db = get_database()

    if not end_date:
        end_date = date.today().isoformat()
    if not start_date:
        start = date.today() - timedelta(days=14)
        start_date = start.isoformat()

    scope = get_role_data_scope(current_user.role)
    if scope == DataScope.BRANCH:
        branch_id = current_user.branch_id

    report_gen = ReportGenerator(db)
    summary = await report_gen.generate_payroll_summary(
        start_date=start_date,
        end_date=end_date,
        branch_id=branch_id
    )

    # Get overtime config
    ot_config = await db.rate_configurations.find_one(
        {"status": "active"},
        {"_id": 0, "tiers": 1, "rules": 1, "name": 1}
    )

    summary["overtime_config"] = ot_config or {"name": "Default", "rules": {}}

    return summary


# ─── Scheduler Info ───

@router.get("/scheduler/status")
async def get_scheduler_status(
    current_user: TokenData = Depends(get_current_user)
):
    """Get scheduler status and next run times."""
    if current_user.role != "SUPER_ADMIN":
        raise ForbiddenException("Only SUPER_ADMIN can view scheduler")

    scheduler = get_scheduler()

    if not scheduler or not scheduler.running:
        return {
            "running": False,
            "jobs": [],
            "message": "Scheduler not active"
        }

    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
            "trigger": str(job.trigger)
        })

    return {
        "running": True,
        "jobs": jobs
    }
