"""
Report Generation Service.
Aggregates attendance data for daily email reports.

Report content:
- Staff clocked in/out
- Total hours per worker
- Total hours per branch
- Late arrivals
- Overtime hours
- Absentees
"""
from datetime import datetime, date, timedelta, timezone
from typing import Dict, List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase


class ReportGenerator:
    """Generates daily attendance and payroll reports."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def generate_daily_report(self, report_date: str = None, branch_id: str = None) -> Dict:
        """
        Generate a full daily report for a specific date.
        If branch_id is None, generates for all branches.
        """
        if not report_date:
            report_date = date.today().isoformat()

        # Get branches
        branch_query = {"status": "active"}
        if branch_id:
            branch_query["id"] = branch_id

        branches = await self.db.branches.find(branch_query, {"_id": 0}).to_list(100)
        branch_map = {b["id"]: b for b in branches}

        # Get all active workers
        user_query = {"status": "active", "role": {"$in": ["WORKER", "TEAM_LEADER"]}}
        if branch_id:
            user_query["branch_id"] = branch_id

        workers = await self.db.users.find(
            user_query,
            {"_id": 0, "id": 1, "first_name": 1, "last_name": 1, "email": 1,
             "employee_id": 1, "branch_id": 1, "hourly_rate_tier": 1}
        ).to_list(1000)
        worker_map = {w["id"]: w for w in workers}  # noqa: F841

        # Get time entries for the date
        entry_query = {"date": report_date}
        if branch_id:
            entry_query["branch_id"] = branch_id

        entries = await self.db.time_entries.find(entry_query, {"_id": 0}).to_list(5000)

        # Build worker entries map
        worker_entries = {}
        for entry in entries:
            uid = entry.get("user_id")
            if uid not in worker_entries:
                worker_entries[uid] = []
            worker_entries[uid].append(entry)

        # Aggregate data
        clocked_in = []
        clocked_out = []
        still_working = []
        late_arrivals = []
        overtime_workers = []
        absentees = []
        worker_hours = []
        branch_hours = {}
        total_hours = 0.0
        total_overtime = 0.0

        for worker in workers:
            uid = worker["id"]
            w_entries = worker_entries.get(uid, [])
            bid = worker.get("branch_id", "")
            branch_name = branch_map.get(bid, {}).get("name", "Unassigned")
            branch_settings = branch_map.get(bid, {}).get("settings", {})

            worker_info = {
                "employee_id": worker.get("employee_id", ""),
                "name": f"{worker.get('first_name', '')} {worker.get('last_name', '')}",
                "email": worker.get("email", ""),
                "branch": branch_name,
                "branch_id": bid
            }

            if not w_entries:
                # Absent
                absentees.append(worker_info)
                continue

            # Process entries
            day_hours = 0.0
            day_ot = 0.0
            is_late = False
            is_clocked_out = True
            clock_in_time = None
            clock_out_time = None

            for entry in w_entries:
                hours = entry.get("total_hours") or 0
                day_hours += hours
                day_ot += entry.get("overtime_hours") or 0

                # Clock in time
                ci = entry.get("clock_in", {})
                if ci and ci.get("timestamp"):
                    clock_in_time = ci["timestamp"]

                # Clock out time
                co = entry.get("clock_out", {})
                if co and co.get("timestamp"):
                    clock_out_time = co["timestamp"]
                else:
                    is_clocked_out = False

                # Late flag
                flags = entry.get("flags", {})
                if flags and flags.get("late_clock_in"):
                    is_late = True

            worker_detail = {
                **worker_info,
                "hours": round(day_hours, 2),
                "overtime_hours": round(day_ot, 2),
                "clock_in": clock_in_time,
                "clock_out": clock_out_time,
            }

            # Categorize
            clocked_in.append(worker_detail)
            if is_clocked_out:
                clocked_out.append(worker_detail)
            else:
                still_working.append(worker_detail)

            if is_late:
                late_threshold = branch_settings.get("late_threshold_minutes", 15)
                worker_detail["late_threshold_minutes"] = late_threshold
                late_arrivals.append(worker_detail)

            if day_ot > 0:
                overtime_workers.append(worker_detail)

            worker_hours.append(worker_detail)
            total_hours += day_hours
            total_overtime += day_ot

            # Branch aggregation
            if bid not in branch_hours:
                branch_hours[bid] = {
                    "branch_name": branch_name,
                    "total_hours": 0,
                    "overtime_hours": 0,
                    "workers_count": 0,
                    "late_count": 0,
                    "absent_count": 0
                }
            branch_hours[bid]["total_hours"] += day_hours
            branch_hours[bid]["overtime_hours"] += day_ot
            branch_hours[bid]["workers_count"] += 1
            if is_late:
                branch_hours[bid]["late_count"] += 1

        # Count absentees per branch
        for absent in absentees:
            bid = absent.get("branch_id", "")
            if bid in branch_hours:
                branch_hours[bid]["absent_count"] += 1
            else:
                branch_name = branch_map.get(bid, {}).get("name", "Unassigned")
                branch_hours[bid] = {
                    "branch_name": branch_name,
                    "total_hours": 0,
                    "overtime_hours": 0,
                    "workers_count": 0,
                    "late_count": 0,
                    "absent_count": 1
                }

        # Round branch hours
        for bid in branch_hours:
            branch_hours[bid]["total_hours"] = round(branch_hours[bid]["total_hours"], 2)
            branch_hours[bid]["overtime_hours"] = round(branch_hours[bid]["overtime_hours"], 2)

        return {
            "report_date": report_date,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "branch_id": branch_id,
            "summary": {
                "total_workers": len(workers),
                "clocked_in": len(clocked_in),
                "clocked_out": len(clocked_out),
                "still_working": len(still_working),
                "late_arrivals": len(late_arrivals),
                "overtime_count": len(overtime_workers),
                "absentees": len(absentees),
                "total_hours": round(total_hours, 2),
                "total_overtime": round(total_overtime, 2)
            },
            "worker_hours": sorted(worker_hours, key=lambda x: x["hours"], reverse=True),
            "late_arrivals": late_arrivals,
            "overtime_workers": overtime_workers,
            "absentees": absentees,
            "branch_breakdown": list(branch_hours.values()),
            "still_working": still_working
        }

    async def generate_payroll_summary(
        self,
        start_date: str,
        end_date: str,
        branch_id: str = None
    ) -> Dict:
        """
        Generate payroll summary with SA BCEA overtime calculations.
        """
        # Get entries for period
        entry_query = {
            "date": {"$gte": start_date, "$lte": end_date},
            "status": {"$in": ["completed", "approved"]}
        }
        if branch_id:
            entry_query["branch_id"] = branch_id

        pipeline = [
            {"$match": entry_query},
            {
                "$group": {
                    "_id": "$user_id",
                    "total_hours": {"$sum": {"$ifNull": ["$total_hours", 0]}},
                    "regular_hours": {"$sum": {"$ifNull": ["$regular_hours", 0]}},
                    "overtime_hours": {"$sum": {"$ifNull": ["$overtime_hours", 0]}},
                    "days_worked": {"$addToSet": "$date"},
                    "entries": {"$sum": 1}
                }
            },
            {
                "$lookup": {
                    "from": "users",
                    "localField": "_id",
                    "foreignField": "id",
                    "as": "user"
                }
            },
            {"$unwind": "$user"},
            {
                "$lookup": {
                    "from": "branches",
                    "localField": "user.branch_id",
                    "foreignField": "id",
                    "as": "branch"
                }
            },
            {"$unwind": {"path": "$branch", "preserveNullAndEmptyArrays": True}},
            {
                "$project": {
                    "_id": 0,
                    "user_id": "$_id",
                    "employee_id": "$user.employee_id",
                    "name": {"$concat": ["$user.first_name", " ", "$user.last_name"]},
                    "email": "$user.email",
                    "branch_name": {"$ifNull": ["$branch.name", "Unassigned"]},
                    "rate_tier": {"$ifNull": ["$user.hourly_rate_tier", "standard"]},
                    "total_hours": {"$round": ["$total_hours", 2]},
                    "regular_hours": {"$round": ["$regular_hours", 2]},
                    "overtime_hours": {"$round": ["$overtime_hours", 2]},
                    "days_worked": {"$size": "$days_worked"},
                    "entries": 1
                }
            },
            {"$sort": {"branch_name": 1, "employee_id": 1}}
        ]

        employee_data = await self.db.time_entries.aggregate(pipeline).to_list(1000)

        # Calculate totals
        total_regular = sum(e.get("regular_hours", 0) for e in employee_data)
        total_ot = sum(e.get("overtime_hours", 0) for e in employee_data)
        total_all = sum(e.get("total_hours", 0) for e in employee_data)

        return {
            "period": {"start": start_date, "end": end_date},
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "branch_id": branch_id,
            "employees": employee_data,
            "totals": {
                "employee_count": len(employee_data),
                "total_regular_hours": round(total_regular, 2),
                "total_overtime_hours": round(total_ot, 2),
                "total_hours": round(total_all, 2)
            }
        }
