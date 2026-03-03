"""
Rate Configuration models and schemas.
Overtime rates are CONFIGURABLE, not hardcoded.
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, List
from datetime import datetime

from models.base import AuditableEntity


class RateTier(BaseModel):
    """Individual rate tier configuration."""
    description: str
    multiplier: float = Field(ge=0)
    applies_after_daily: Optional[float] = None  # Hours threshold
    applies_after_weekly: Optional[float] = None  # Hours threshold


# Database Model
class RateConfiguration(AuditableEntity):
    """Rate configuration database model."""
    name: str
    code: str
    effective_date: str  # YYYY-MM-DD
    expiry_date: Optional[str] = None
    status: str = "active"
    
    # Rate tiers (configurable)
    tiers: Dict[str, RateTier] = Field(default_factory=lambda: {
        "standard": RateTier(description="Regular hourly rate", multiplier=1.0),
        "standard_ot": RateTier(
            description="Standard overtime (1.5x)",
            multiplier=1.5,
            applies_after_daily=8.0,
            applies_after_weekly=40.0
        ),
        "double_ot": RateTier(
            description="Double time overtime (2x)",
            multiplier=2.0,
            applies_after_daily=12.0,
            applies_after_weekly=60.0
        ),
        "holiday": RateTier(description="Holiday rate", multiplier=2.0),
        "weekend": RateTier(description="Weekend rate", multiplier=1.25)
    })
    
    # Branch-specific overrides
    branch_overrides: Dict[str, Dict[str, RateTier]] = Field(default_factory=dict)


# API Schemas
class RateConfigCreate(BaseModel):
    """Schema for creating rate configuration."""
    name: str = Field(min_length=1, max_length=200)
    code: str = Field(min_length=1, max_length=50)
    effective_date: str
    expiry_date: Optional[str] = None
    tiers: Dict[str, RateTier]
    branch_overrides: Dict[str, Dict[str, RateTier]] = Field(default_factory=dict)


class RateConfigUpdate(BaseModel):
    """Schema for updating rate configuration."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    expiry_date: Optional[str] = None
    tiers: Optional[Dict[str, RateTier]] = None
    branch_overrides: Optional[Dict[str, Dict[str, RateTier]]] = None
    status: Optional[str] = None


class RateConfigResponse(BaseModel):
    """Schema for rate configuration response."""
    id: str
    name: str
    code: str
    effective_date: str
    expiry_date: Optional[str] = None
    status: str
    tiers: Dict[str, RateTier]
    branch_overrides: Dict[str, Dict[str, RateTier]]
    created_at: datetime
    updated_at: datetime


class RateConfigListResponse(BaseModel):
    """Schema for rate configuration list."""
    configs: List[RateConfigResponse]
    total: int
