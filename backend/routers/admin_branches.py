"""
Branches management router.
"""
from fastapi import APIRouter, Depends, Query, Request
from typing import Optional, List
from pydantic import BaseModel

from core.database import get_database
from core.security import get_current_user, TokenData
from core.exceptions import ForbiddenException, NotFoundException, ConflictException
from middleware.permissions import require_permission
from models.role import has_permission, get_role_data_scope, DataScope
from models.branch import BranchCreate, BranchUpdate, Address, Geofence, BranchSettings, GeoPoint
from models.base import generate_uuid, utc_now
from services.audit_service import audit_log

router = APIRouter(prefix="/admin/branches", tags=["Branch Management"])


@router.get("/list")
async def list_branches(
    status: Optional[str] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: TokenData = Depends(get_current_user)
):
    """List branches."""
    db = get_database()
    
    scope = get_role_data_scope(current_user.role)
    
    query = {}
    
    # Scope restrictions
    if scope == DataScope.BRANCH:
        query["id"] = current_user.branch_id
    
    if status:
        query["status"] = status
    
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"code": {"$regex": search, "$options": "i"}}
        ]
    
    total = await db.branches.count_documents(query)
    
    branches = await db.branches.find(query, {"_id": 0}) \
        .sort("name", 1) \
        .skip((page - 1) * page_size) \
        .limit(page_size) \
        .to_list(page_size)
    
    # Add worker counts
    for branch in branches:
        branch["worker_count"] = await db.users.count_documents({
            "branch_id": branch["id"],
            "role": "WORKER",
            "status": "active"
        })
    
    return {
        "branches": branches,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/{branch_id}")
async def get_branch(
    branch_id: str,
    current_user: TokenData = Depends(get_current_user)
):
    """Get branch details."""
    db = get_database()
    
    scope = get_role_data_scope(current_user.role)
    if scope == DataScope.BRANCH and branch_id != current_user.branch_id:
        raise ForbiddenException("Cannot access this branch")
    
    branch = await db.branches.find_one({"id": branch_id}, {"_id": 0})
    if not branch:
        raise NotFoundException("Branch", branch_id)
    
    # Get stats
    worker_count = await db.users.count_documents({
        "branch_id": branch_id,
        "role": "WORKER",
        "status": "active"
    })
    
    team_count = await db.teams.count_documents({
        "branch_id": branch_id,
        "status": "active"
    })
    
    return {
        "branch": branch,
        "stats": {
            "worker_count": worker_count,
            "team_count": team_count
        }
    }


@router.post("/create")
async def create_branch(
    branch_data: BranchCreate,
    req: Request,
    current_user: TokenData = Depends(get_current_user)
):
    """Create a new branch."""
    db = get_database()
    
    if not has_permission(current_user.role, "branches.create"):
        raise ForbiddenException("Cannot create branches")
    
    # Check code uniqueness
    existing = await db.branches.find_one({"code": branch_data.code})
    if existing:
        raise ConflictException("Branch code already exists")
    
    now = utc_now()
    
    branch = {
        "id": generate_uuid(),
        "name": branch_data.name,
        "code": branch_data.code,
        "status": "active",
        "address": branch_data.address.model_dump() if branch_data.address else {},
        "geofence": branch_data.geofence.model_dump() if branch_data.geofence else None,
        "timezone": branch_data.timezone,
        "settings": branch_data.settings.model_dump() if branch_data.settings else BranchSettings().model_dump(),
        "admin_ids": branch_data.admin_ids,
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
        "created_by": current_user.user_id
    }
    
    await db.branches.insert_one(branch)
    
    await audit_log(
        db=db,
        actor_id=current_user.user_id,
        actor_email=current_user.email,
        actor_role=current_user.role,
        action="branch.create",
        target_type="branch",
        target_id=branch["id"],
        target_ref=f"{branch['name']} ({branch['code']})",
        request=req
    )
    
    branch.pop("_id", None)
    return {"message": "Branch created", "branch": branch}


@router.put("/{branch_id}")
async def update_branch(
    branch_id: str,
    update_data: BranchUpdate,
    req: Request,
    current_user: TokenData = Depends(get_current_user)
):
    """Update a branch."""
    db = get_database()
    
    if not has_permission(current_user.role, "branches.update"):
        raise ForbiddenException("Cannot update branches")
    
    scope = get_role_data_scope(current_user.role)
    if scope == DataScope.BRANCH and branch_id != current_user.branch_id:
        raise ForbiddenException("Cannot update this branch")
    
    branch = await db.branches.find_one({"id": branch_id}, {"_id": 0})
    if not branch:
        raise NotFoundException("Branch", branch_id)
    
    updates = {"updated_at": utc_now().isoformat()}
    update_dict = update_data.model_dump(exclude_unset=True)
    
    for field, value in update_dict.items():
        if value is not None:
            if hasattr(value, "model_dump"):
                updates[field] = value.model_dump()
            else:
                updates[field] = value
    
    await db.branches.update_one({"id": branch_id}, {"$set": updates})
    
    await audit_log(
        db=db,
        actor_id=current_user.user_id,
        actor_email=current_user.email,
        actor_role=current_user.role,
        action="branch.update",
        target_type="branch",
        target_id=branch_id,
        changes={"before": branch, "after": updates},
        request=req
    )
    
    updated = await db.branches.find_one({"id": branch_id}, {"_id": 0})
    return {"message": "Branch updated", "branch": updated}


@router.put("/{branch_id}/geofence")
async def update_branch_geofence(
    branch_id: str,
    geofence: Geofence,
    req: Request,
    current_user: TokenData = Depends(get_current_user)
):
    """Update branch geofence settings."""
    db = get_database()
    
    if not has_permission(current_user.role, "branches.update"):
        raise ForbiddenException("Cannot update branch geofence")
    
    branch = await db.branches.find_one({"id": branch_id}, {"_id": 0})
    if not branch:
        raise NotFoundException("Branch", branch_id)
    
    now = utc_now()
    
    await db.branches.update_one(
        {"id": branch_id},
        {
            "$set": {
                "geofence": geofence.model_dump(),
                "updated_at": now.isoformat()
            }
        }
    )
    
    await audit_log(
        db=db,
        actor_id=current_user.user_id,
        actor_email=current_user.email,
        actor_role=current_user.role,
        action="branch.geofence_update",
        target_type="branch",
        target_id=branch_id,
        changes={
            "before": {"geofence": branch.get("geofence")},
            "after": {"geofence": geofence.model_dump()}
        },
        request=req
    )
    
    return {"message": "Geofence updated"}
