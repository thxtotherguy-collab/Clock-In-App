"""
Audit service for tracking all system changes.
"""
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from fastapi import Request
from motor.motor_asyncio import AsyncIOMotorDatabase

from models.audit import AuditLog, AuditChanges, AUDIT_ACTIONS, get_action_description
from models.base import generate_uuid


class AuditService:
    """Service for creating and querying audit logs."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db.audit_logs
    
    async def log(
        self,
        actor_id: str,
        actor_email: str,
        actor_role: str,
        action: str,
        target_type: str,
        target_id: str,
        target_ref: Optional[str] = None,
        branch_id: Optional[str] = None,
        team_id: Optional[str] = None,
        changes: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        request: Optional[Request] = None
    ) -> str:
        """Create an audit log entry."""
        
        # Extract client info from request
        actor_ip = None
        actor_device = None
        if request:
            actor_ip = self._get_client_ip(request)
            actor_device = request.headers.get("User-Agent", "")[:200]
        
        # Prepare changes
        audit_changes = None
        if changes:
            audit_changes = AuditChanges(
                before=changes.get("before", {}),
                after=changes.get("after", {})
            )
        
        timestamp = datetime.now(timezone.utc)
        
        audit_entry = {
            "id": generate_uuid(),
            "actor_id": actor_id,
            "actor_email": actor_email,
            "actor_role": actor_role,
            "actor_ip": actor_ip,
            "actor_device": actor_device,
            "action": action,
            "action_category": action.split(".")[0],
            "description": get_action_description(action),
            "target_type": target_type,
            "target_id": target_id,
            "target_ref": target_ref,
            "branch_id": branch_id,
            "team_id": team_id,
            "changes": audit_changes.model_dump() if audit_changes else None,
            "metadata": metadata or {},
            "timestamp": timestamp.isoformat(),
            "created_at": timestamp.isoformat()
        }
        
        await self.collection.insert_one(audit_entry)
        return audit_entry["id"]
    
    async def get_logs(
        self,
        actor_id: Optional[str] = None,
        action_category: Optional[str] = None,
        target_type: Optional[str] = None,
        target_id: Optional[str] = None,
        branch_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 50
    ) -> tuple:
        """Query audit logs with filters."""
        
        query = {}
        
        if actor_id:
            query["actor_id"] = actor_id
        if action_category:
            query["action_category"] = action_category
        if target_type:
            query["target_type"] = target_type
        if target_id:
            query["target_id"] = target_id
        if branch_id:
            query["branch_id"] = branch_id
        
        if start_date or end_date:
            query["timestamp"] = {}
            if start_date:
                query["timestamp"]["$gte"] = start_date.isoformat()
            if end_date:
                query["timestamp"]["$lte"] = end_date.isoformat()
        
        # Get total count
        total = await self.collection.count_documents(query)
        
        # Get paginated results
        skip = (page - 1) * page_size
        cursor = self.collection.find(query, {"_id": 0})
        cursor = cursor.sort("timestamp", -1).skip(skip).limit(page_size)
        logs = await cursor.to_list(page_size)
        
        return logs, total
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request."""
        # Check forwarded headers first (for reverse proxy)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fall back to direct client
        if request.client:
            return request.client.host
        
        return "unknown"


# Helper function for quick audit logging
async def audit_log(
    db: AsyncIOMotorDatabase,
    actor_id: str,
    actor_email: str,
    actor_role: str,
    action: str,
    target_type: str,
    target_id: str,
    **kwargs
):
    """Quick helper to create audit log."""
    service = AuditService(db)
    return await service.log(
        actor_id=actor_id,
        actor_email=actor_email,
        actor_role=actor_role,
        action=action,
        target_type=target_type,
        target_id=target_id,
        **kwargs
    )
