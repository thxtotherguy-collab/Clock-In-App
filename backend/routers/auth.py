"""
Authentication router - JWT login/register.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, EmailStr
from datetime import datetime, timezone
from typing import Optional

from core.database import get_database
from core.security import (
    verify_password, get_password_hash, create_tokens,
    get_current_user, TokenData, TokenResponse, decode_token
)
from core.exceptions import UnauthorizedException, BadRequestException, ConflictException
from models.user import User, UserRole, UserStatus
from models.base import generate_uuid, utc_now
from services.audit_service import audit_log

router = APIRouter(prefix="/auth", tags=["Authentication"])


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    employee_id: Optional[str] = None


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict


class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, req: Request):
    """Authenticate user and return JWT tokens."""
    db = get_database()
    
    # Find user by email
    user = await db.users.find_one(
        {"email": request.email.lower()},
        {"_id": 0}
    )
    
    if not user:
        raise UnauthorizedException("Invalid email or password")
    
    # Check password
    if not verify_password(request.password, user["password_hash"]):
        raise UnauthorizedException("Invalid email or password")
    
    # Check user status
    if user["status"] != "active":
        raise UnauthorizedException("Account is not active")
    
    # Create tokens
    token_data = {
        "user_id": user["id"],
        "email": user["email"],
        "role": user["role"],
        "branch_id": user.get("branch_id"),
        "team_id": user.get("team_id")
    }
    tokens = create_tokens(token_data)
    
    # Update last login
    await db.users.update_one(
        {"id": user["id"]},
        {"$set": {"last_login_at": utc_now().isoformat()}}
    )
    
    # Audit log
    await audit_log(
        db=db,
        actor_id=user["id"],
        actor_email=user["email"],
        actor_role=user["role"],
        action="auth.login",
        target_type="user",
        target_id=user["id"],
        request=req
    )
    
    # Return user info (without sensitive data)
    user_response = {
        "id": user["id"],
        "email": user["email"],
        "first_name": user["first_name"],
        "last_name": user["last_name"],
        "role": user["role"],
        "branch_id": user.get("branch_id"),
        "team_id": user.get("team_id"),
        "employee_id": user.get("employee_id")
    }
    
    return LoginResponse(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        token_type=tokens.token_type,
        expires_in=tokens.expires_in,
        user=user_response
    )


@router.post("/register", response_model=LoginResponse)
async def register(request: RegisterRequest, req: Request):
    """Register a new worker account."""
    db = get_database()
    
    # Check if email exists
    existing = await db.users.find_one({"email": request.email.lower()})
    if existing:
        raise ConflictException("Email already registered")
    
    # Generate employee_id if not provided
    employee_id = request.employee_id
    if not employee_id:
        # Generate a unique employee_id based on email and timestamp
        timestamp = utc_now().strftime("%m%d%H%M")
        username = request.email.split('@')[0][:4].upper()
        employee_id = f"{username}{timestamp}"
    
    # Check employee_id uniqueness
    existing_emp = await db.users.find_one({"employee_id": employee_id})
    if existing_emp:
        raise ConflictException("Employee ID already exists")
    
    # Create user
    now = utc_now()
    user = {
        "id": generate_uuid(),
        "email": request.email.lower(),
        "password_hash": get_password_hash(request.password),
        "first_name": request.first_name,
        "last_name": request.last_name,
        "phone": request.phone,
        "employee_id": employee_id,
        "role": UserRole.WORKER.value,
        "status": UserStatus.ACTIVE.value,
        "branch_id": None,
        "team_id": None,
        "job_site_ids": [],
        "profile_photo_url": None,
        "hourly_rate_tier": "standard",
        "overtime_eligible": True,
        "default_shift_id": None,
        "permission_overrides": {},
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
        "last_login_at": now.isoformat()
    }
    
    await db.users.insert_one(user)
    
    # Create tokens
    token_data = {
        "user_id": user["id"],
        "email": user["email"],
        "role": user["role"],
        "branch_id": user.get("branch_id"),
        "team_id": user.get("team_id")
    }
    tokens = create_tokens(token_data)
    
    # Audit log
    await audit_log(
        db=db,
        actor_id=user["id"],
        actor_email=user["email"],
        actor_role=user["role"],
        action="user.create",
        target_type="user",
        target_id=user["id"],
        request=req
    )
    
    user_response = {
        "id": user["id"],
        "email": user["email"],
        "first_name": user["first_name"],
        "last_name": user["last_name"],
        "role": user["role"],
        "branch_id": user.get("branch_id"),
        "team_id": user.get("team_id"),
        "employee_id": user.get("employee_id")
    }
    
    return LoginResponse(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        token_type=tokens.token_type,
        expires_in=tokens.expires_in,
        user=user_response
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshRequest):
    """Refresh access token using refresh token."""
    db = get_database()
    
    # Decode refresh token
    payload = decode_token(request.refresh_token)
    
    if payload.get("type") != "refresh":
        raise UnauthorizedException("Invalid refresh token")
    
    user_id = payload.get("user_id")
    
    # Get user
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user or user["status"] != "active":
        raise UnauthorizedException("User not found or inactive")
    
    # Create new tokens
    token_data = {
        "user_id": user["id"],
        "email": user["email"],
        "role": user["role"],
        "branch_id": user.get("branch_id"),
        "team_id": user.get("team_id")
    }
    
    return create_tokens(token_data)


@router.get("/me")
async def get_current_user_info(current_user: TokenData = Depends(get_current_user)):
    """Get current authenticated user info."""
    db = get_database()
    
    user = await db.users.find_one(
        {"id": current_user.user_id},
        {"_id": 0, "password_hash": 0}
    )
    
    if not user:
        raise UnauthorizedException("User not found")
    
    # Get branch info if assigned
    branch = None
    if user.get("branch_id"):
        branch = await db.branches.find_one(
            {"id": user["branch_id"]},
            {"_id": 0, "id": 1, "name": 1, "code": 1, "geofence": 1, "settings": 1}
        )
    
    # Get team info if assigned
    team = None
    if user.get("team_id"):
        team = await db.teams.find_one(
            {"id": user["team_id"]},
            {"_id": 0, "id": 1, "name": 1, "code": 1}
        )
    
    return {
        "user": user,
        "branch": branch,
        "team": team
    }
