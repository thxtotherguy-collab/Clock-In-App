"""
Overtime calculation service.
Rates and thresholds are loaded from configuration - NOT hardcoded.
"""
from datetime import datetime, date, timedelta, timezone
from typing import List, Dict, Optional, Tuple
from motor.motor_asyncio import AsyncIOMotorDatabase

from models.overtime import OvertimeRecord, OvertimeStatus, PeriodType
from models.time_entry import TimeEntry
from models.rate_config import RateConfiguration
from models.base import generate_uuid, utc_now


class OvertimeCalculator:
    """
    Calculates overtime based on configurable thresholds and rate tiers.
    All rates are loaded from RateConfiguration collection.
    """
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
    
    async def get_active_rate_config(self, effective_date: str = None) -> Optional[Dict]:
        """Get the active rate configuration."""
        if not effective_date:
            effective_date = date.today().isoformat()
        
        config = await self.db.rate_configurations.find_one(
            {
                "status": "active",
                "effective_date": {"$lte": effective_date},
                "$or": [
                    {"expiry_date": None},
                    {"expiry_date": {"$gte": effective_date}}
                ]
            },
            {"_id": 0},
            sort=[("effective_date", -1)]
        )
        return config
    
    async def get_branch_settings(self, branch_id: str) -> Dict:
        """Get branch-specific overtime settings."""
        branch = await self.db.branches.find_one(
            {"id": branch_id},
            {"_id": 0, "settings": 1}
        )
        if branch and "settings" in branch:
            return branch["settings"]
        
        # Default settings
        return {
            "overtime_threshold_daily": 8.0,
            "overtime_threshold_weekly": 40.0
        }
    
    def get_effective_threshold(
        self,
        rate_config: Dict,
        branch_id: str,
        period_type: str
    ) -> float:
        """Get effective overtime threshold considering branch overrides."""
        
        # Check branch overrides first
        if branch_id in rate_config.get("branch_overrides", {}):
            branch_config = rate_config["branch_overrides"][branch_id]
            if "standard_ot" in branch_config:
                tier = branch_config["standard_ot"]
                key = f"applies_after_{period_type}"
                if key in tier:
                    return tier[key]
        
        # Use default tier threshold
        standard_ot = rate_config.get("tiers", {}).get("standard_ot", {})
        key = f"applies_after_{period_type}"
        return standard_ot.get(key, 8.0 if period_type == "daily" else 40.0)
    
    def get_rate_multiplier(
        self,
        rate_config: Dict,
        branch_id: str,
        tier_name: str
    ) -> float:
        """Get rate multiplier for a tier considering branch overrides."""
        
        # Check branch overrides first
        if branch_id in rate_config.get("branch_overrides", {}):
            branch_config = rate_config["branch_overrides"][branch_id]
            if tier_name in branch_config:
                return branch_config[tier_name].get("multiplier", 1.0)
        
        # Use default tier multiplier
        tier = rate_config.get("tiers", {}).get(tier_name, {})
        return tier.get("multiplier", 1.0)
    
    def determine_rate_tier(
        self,
        hours_worked: float,
        rate_config: Dict,
        branch_id: str,
        period_type: str
    ) -> Tuple[str, float]:
        """Determine applicable rate tier based on hours worked."""
        
        tiers = rate_config.get("tiers", {})
        
        # Check from highest tier to lowest
        # Double OT
        double_ot = tiers.get("double_ot", {})
        double_threshold = double_ot.get(f"applies_after_{period_type}", 12.0)
        if hours_worked > double_threshold:
            multiplier = self.get_rate_multiplier(rate_config, branch_id, "double_ot")
            return "double_ot", multiplier
        
        # Standard OT
        standard_ot = tiers.get("standard_ot", {})
        standard_threshold = standard_ot.get(f"applies_after_{period_type}", 8.0)
        if hours_worked > standard_threshold:
            multiplier = self.get_rate_multiplier(rate_config, branch_id, "standard_ot")
            return "standard_ot", multiplier
        
        # Regular rate
        return "standard", 1.0
    
    async def calculate_daily_overtime(
        self,
        user_id: str,
        entry_date: str,
        branch_id: str
    ) -> Optional[Dict]:
        """Calculate overtime for a single day."""
        
        # Get rate configuration
        rate_config = await self.get_active_rate_config(entry_date)
        if not rate_config:
            return None
        
        # Get time entries for the day
        entries = await self.db.time_entries.find(
            {
                "user_id": user_id,
                "date": entry_date,
                "status": {"$in": ["completed", "approved"]}
            },
            {"_id": 0}
        ).to_list(100)
        
        if not entries:
            return None
        
        # Calculate total hours
        total_hours = sum(e.get("total_hours", 0) or 0 for e in entries)
        
        # Get threshold
        threshold = self.get_effective_threshold(rate_config, branch_id, "daily")
        
        # Check if overtime
        if total_hours <= threshold:
            return None
        
        overtime_hours = total_hours - threshold
        tier, multiplier = self.determine_rate_tier(
            total_hours, rate_config, branch_id, "daily"
        )
        
        return {
            "period_type": PeriodType.DAILY.value,
            "period_start": entry_date,
            "period_end": entry_date,
            "threshold_hours": threshold,
            "total_worked_hours": total_hours,
            "overtime_hours": overtime_hours,
            "rate_tier": tier,
            "rate_multiplier": multiplier,
            "time_entry_ids": [e["id"] for e in entries]
        }
    
    async def calculate_weekly_overtime(
        self,
        user_id: str,
        week_start: str,  # Monday YYYY-MM-DD
        branch_id: str
    ) -> Optional[Dict]:
        """Calculate overtime for a week."""
        
        # Get rate configuration
        rate_config = await self.get_active_rate_config(week_start)
        if not rate_config:
            return None
        
        # Calculate week end (Sunday)
        start_date = datetime.strptime(week_start, "%Y-%m-%d")
        end_date = start_date + timedelta(days=6)
        week_end = end_date.strftime("%Y-%m-%d")
        
        # Get time entries for the week
        entries = await self.db.time_entries.find(
            {
                "user_id": user_id,
                "date": {"$gte": week_start, "$lte": week_end},
                "status": {"$in": ["completed", "approved"]}
            },
            {"_id": 0}
        ).to_list(100)
        
        if not entries:
            return None
        
        # Calculate total weekly hours
        total_hours = sum(e.get("total_hours", 0) or 0 for e in entries)
        
        # Get weekly threshold
        threshold = self.get_effective_threshold(rate_config, branch_id, "weekly")
        
        # Check if weekly overtime
        if total_hours <= threshold:
            return None
        
        overtime_hours = total_hours - threshold
        tier, multiplier = self.determine_rate_tier(
            total_hours, rate_config, branch_id, "weekly"
        )
        
        return {
            "period_type": PeriodType.WEEKLY.value,
            "period_start": week_start,
            "period_end": week_end,
            "threshold_hours": threshold,
            "total_worked_hours": total_hours,
            "overtime_hours": overtime_hours,
            "rate_tier": tier,
            "rate_multiplier": multiplier,
            "time_entry_ids": [e["id"] for e in entries]
        }
    
    async def create_overtime_record(
        self,
        user_id: str,
        branch_id: str,
        team_id: Optional[str],
        overtime_data: Dict
    ) -> Dict:
        """Create an overtime record in the database."""
        
        now = utc_now()
        
        record = {
            "id": generate_uuid(),
            "user_id": user_id,
            "branch_id": branch_id,
            "team_id": team_id,
            "period_type": overtime_data["period_type"],
            "period_start": overtime_data["period_start"],
            "period_end": overtime_data["period_end"],
            "threshold_hours": overtime_data["threshold_hours"],
            "total_worked_hours": overtime_data["total_worked_hours"],
            "overtime_hours": overtime_data["overtime_hours"],
            "rate_tier": overtime_data["rate_tier"],
            "rate_multiplier": overtime_data["rate_multiplier"],
            "time_entry_ids": overtime_data["time_entry_ids"],
            "status": OvertimeStatus.PENDING.value,
            "requires_approval": True,
            "approval": {
                "approved_by": None,
                "approved_at": None,
                "rejected_reason": None
            },
            "exported": False,
            "export_batch_id": None,
            "exported_at": None,
            "calculated_at": now.isoformat(),
            "created_at": now.isoformat(),
            "updated_at": now.isoformat()
        }
        
        await self.db.overtime_records.insert_one(record)
        
        # Return without _id
        record.pop("_id", None)
        return record
