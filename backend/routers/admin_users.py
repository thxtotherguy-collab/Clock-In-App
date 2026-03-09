"""
Users management router - CRUD operations for admin.
"""
from fastapi import APIRouter, Depends, Query, Request
from typing import Optional, List
from pydantic import BaseModel, EmailStr

from core.database import get_database
from core.security import get_current_user, TokenData, get_password_hash
from core.exceptions import ForbiddenException, NotFoundException, ConflictException
from middleware.permissions import require_permission
from models.role import has_permission, get_role_data_scope, DataScope, can_manage_role
from models.user import UserRole, UserStatus
from models.base import generate_uuid, utc_now
from services.audit_service import audit_log

router = APIRouter(prefix="/admin/users", tags=["User Management"])


class UserCreateAdmin(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    employee_id: Optional[str] = None
    role: UserRole = UserRole.WORKER
    branch_id: Optional[str] = None
    team_id: Optional[str] = None
    hourly_rate_tier: str = "standard"
    overtime_eligible: bool = True


class UserUpdateAdmin(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    employee_id: Optional[str] = None
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None
    branch_id: Optional[str] = None
    team_id: Optional[str] = None
    hourly_rate_tier: Optional[str] = None
    overtime_eligible: Optional[bool] = None


@router.get("/list")
async def list_users(
    branch_id: Optional[str] = None,
    team_id: Optional[str] = None,
    role: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: TokenData = Depends(get_current_user)
):
    """List users with filtering."""
    db = get_database()
    
    if not has_permission(current_user.role, "users.view_branch"):
        if not has_permission(current_user.role, "users.view_team"):
            raise ForbiddenException("Cannot view users")
    
    scope = get_role_data_scope(current_user.role)
    
    # Build query
    query = {}
    
    # Apply scope
    if scope == DataScope.BRANCH:
        query["branch_id"] = current_user.branch_id
    elif scope == DataScope.TEAM:
        query["team_id"] = current_user.team_id
    elif branch_id and scope == DataScope.ALL:
        query["branch_id"] = branch_id
    
    if team_id:
        query["team_id"] = team_id
    if role:
        query["role"] = role
    if status:
        query["status"] = status
    
    # Search by name or email
    if search:
        query["$or"] = [
            {"first_name": {"$regex": search, "$options": "i"}},
            {"last_name": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}},
            {"employee_id": {"$regex": search, "$options": "i"}}
        ]
    
    # Get total
    total = await db.users.count_documents(query)
    
    # Get users
    pipeline = [
        {"$match": query},
        {"$sort": {"created_at": -1}},
        {"$skip": (page - 1) * page_size},
        {"$limit": page_size},
        {
            "$lookup": {
                "from": "branches",
                "localField": "branch_id",
                "foreignField": "id",
                "as": "branch"
            }
        },
        {"$unwind": {"path": "$branch", "preserveNullAndEmptyArrays": True}},
        {
            "$lookup": {
                "from": "teams",
                "localField": "team_id",
                "foreignField": "id",
                "as": "team"
            }
        },
        {"$unwind": {"path": "$team", "preserveNullAndEmptyArrays": True}},
        {
            "$project": {
                "_id": 0,
                "id": 1,
                "email": 1,
                "first_name": 1,
                "last_name": 1,
                "phone": 1,
                "employee_id": 1,
                "role": 1,
                "status": 1,
                "branch_id": 1,
                "branch_name": "$branch.name",
                "team_id": 1,
                "team_name": "$team.name",
                "hourly_rate_tier": 1,
                "overtime_eligible": 1,
                "created_at": 1,
                "last_login_at": 1
            }
        }
    ]
    
    users = await db.users.aggregate(pipeline).to_list(page_size)
    
    return {
        "users": users,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }


@router.post("/create")
async def create_user(
    user_data: UserCreateAdmin,
    req: Request,
    current_user: TokenData = Depends(get_current_user)
):
    """Create a new user."""
    db = get_database()
    
    if not has_permission(current_user.role, "users.create"):
        raise ForbiddenException("Cannot create users")
    
    # Check if can create this role
    if not can_manage_role(current_user.role, user_data.role.value):
        raise ForbiddenException(f"Cannot create user with role {user_data.role}")
    
    # Check scope
    scope = get_role_data_scope(current_user.role)
    if scope == DataScope.BRANCH:
        # Branch admin can only create users in their branch
        user_data.branch_id = current_user.branch_id
    
    # Check email uniqueness
    existing = await db.users.find_one({"email": user_data.email.lower()})
    if existing:
        raise ConflictException("Email already exists")
    
    # Check employee_id uniqueness
    if user_data.employee_id:
        existing_emp = await db.users.find_one({"employee_id": user_data.employee_id})
        if existing_emp:
            raise ConflictException("Employee ID already exists")
    
    now = utc_now()
    
    user = {
        "id": generate_uuid(),
        "email": user_data.email.lower(),
        "password_hash": get_password_hash(user_data.password),
        "first_name": user_data.first_name,
        "last_name": user_data.last_name,
        "phone": user_data.phone,
        "employee_id": user_data.employee_id,
        "role": user_data.role.value,
        "status": UserStatus.ACTIVE.value,
        "branch_id": user_data.branch_id,
        "team_id": user_data.team_id,
        "job_site_ids": [],
        "hourly_rate_tier": user_data.hourly_rate_tier,
        "overtime_eligible": user_data.overtime_eligible,
        "permission_overrides": {},
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
        "created_by": current_user.user_id
    }
    
    await db.users.insert_one(user)
    
    # Audit log
    await audit_log(
        db=db,
        actor_id=current_user.user_id,
        actor_email=current_user.email,
        actor_role=current_user.role,
        action="user.create",
        target_type="user",
        target_id=user["id"],
        target_ref=f"{user['first_name']} {user['last_name']} ({user['email']})",
        branch_id=user.get("branch_id"),
        request=req
    )
    
    # Return without sensitive data
    user.pop("password_hash", None)
    user.pop("_id", None)
    
    return {"message": "User created", "user": user}


@router.put("/{user_id}")
async def update_user(
    user_id: str,
    update_data: UserUpdateAdmin,
    req: Request,
    current_user: TokenData = Depends(get_current_user)
):
    """Update a user."""
    db = get_database()
    
    if not has_permission(current_user.role, "users.update_others"):
        raise ForbiddenException("Cannot update users")
    
    # Get existing user
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise NotFoundException("User", user_id)
    
    # Check scope
    scope = get_role_data_scope(current_user.role)
    if scope == DataScope.BRANCH and user.get("branch_id") != current_user.branch_id:
        raise ForbiddenException("Cannot update users outside your branch")
    
    # Check if can manage this role
    if update_data.role and not can_manage_role(current_user.role, update_data.role.value):
        raise ForbiddenException(f"Cannot assign role {update_data.role}")
    
    # Build updates
    updates = {"updated_at": utc_now().isoformat()}
    update_dict = update_data.model_dump(exclude_unset=True)
    
    for field, value in update_dict.items():
        if value is not None:
            if field == "role":
                updates[field] = value.value
            elif field == "status":
                updates[field] = value.value
            else:
                updates[field] = value
    
    # Check employee_id uniqueness if changing
    if "employee_id" in updates and updates["employee_id"]:
        existing = await db.users.find_one({
            "employee_id": updates["employee_id"],
            "id": {"$ne": user_id}
        })
        if existing:
            raise ConflictException("Employee ID already exists")
    
    await db.users.update_one({"id": user_id}, {"$set": updates})
    
    # Audit log
    await audit_log(
        db=db,
        actor_id=current_user.user_id,
        actor_email=current_user.email,
        actor_role=current_user.role,
        action="user.update",
        target_type="user",
        target_id=user_id,
        changes={"before": user, "after": updates},
        request=req
    )
    
    updated_user = await db.users.find_one({"id": user_id}, {"_id": 0, "password_hash": 0})
    
    return {"message": "User updated", "user": updated_user}


@router.delete("/{user_id}")
async def deactivate_user(
    user_id: str,
    req: Request,
    current_user: TokenData = Depends(get_current_user)
):
    """Deactivate (soft delete) a user."""
    db = get_database()
    
    if not has_permission(current_user.role, "users.delete"):
        raise ForbiddenException("Cannot delete users")
    
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise NotFoundException("User", user_id)
    
    # Check scope
    scope = get_role_data_scope(current_user.role)
    if scope == DataScope.BRANCH and user.get("branch_id") != current_user.branch_id:
        raise ForbiddenException("Cannot delete users outside your branch")
    
    # Soft delete
    now = utc_now()
    await db.users.update_one(
        {"id": user_id},
        {
            "$set": {
                "status": UserStatus.INACTIVE.value,
                "updated_at": now.isoformat(),
                "deleted_at": now.isoformat(),
                "deleted_by": current_user.user_id
            }
        }
    )
    
    # Audit log
    await audit_log(
        db=db,
        actor_id=current_user.user_id,
        actor_email=current_user.email,
        actor_role=current_user.role,
        action="user.delete",
        target_type="user",
        target_id=user_id,
        request=req
    )
    
    return {"message": "User deactivated"}
