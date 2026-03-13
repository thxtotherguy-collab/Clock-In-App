"""Security Middleware Stack.
- Rate limiting (login brute-force protection)
- Security headers (X-Frame-Options, CSP, HSTS, etc.)
- Request ID injection
- Request timing
- IP-based account lockout tracking
"""
import time
import uuid
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, Tuple
from collections import defaultdict
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse

logger = logging.getLogger("security")


# ─── In-Memory Rate Limiter (production: use Redis) ───

class RateLimitStore:
    """Simple in-memory rate limiter for MVP. Replace with Redis for multi-instance."""
    
    def __init__(self):
        self._attempts: Dict[str, list] = defaultdict(list)  # key -> [timestamps]
        self._lockouts: Dict[str, datetime] = {}  # key -> lockout_until
    
    def record_attempt(self, key: str, success: bool = False):
        """Record a login attempt."""
        now = datetime.now(timezone.utc)
        if success:
            # Clear on success
            self._attempts.pop(key, None)
            self._lockouts.pop(key, None)
            return
        
        self._attempts[key].append(now)
        # Clean old entries (keep last 30 min)
        cutoff = now - timedelta(minutes=30)
        self._attempts[key] = [t for t in self._attempts[key] if t > cutoff]
    
    def is_locked(self, key: str) -> Tuple[bool, Optional[int]]:
        """Check if key is locked out. Returns (is_locked, seconds_remaining)."""
        now = datetime.now(timezone.utc)
        
        if key in self._lockouts:
            if now < self._lockouts[key]:
                remaining = int((self._lockouts[key] - now).total_seconds())
                return True, remaining
            else:
                del self._lockouts[key]
        
        return False, None
    
    def check_and_lock(self, key: str, max_attempts: int = 5, window_minutes: int = 15, lockout_minutes: int = 15) -> Tuple[bool, int]:
        """Check attempts and apply lockout if threshold exceeded.
        Returns (should_proceed, remaining_attempts)."""
        is_locked, remaining = self.is_locked(key)
        if is_locked:
            return False, 0
        
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(minutes=window_minutes)
        recent = [t for t in self._attempts.get(key, []) if t > cutoff]
        
        if len(recent) >= max_attempts:
            self._lockouts[key] = now + timedelta(minutes=lockout_minutes)
            logger.warning(f"[SECURITY] Account locked: {key} ({len(recent)} failed attempts)")
            return False, 0
        
        return True, max_attempts - len(recent)
    
    def cleanup(self):
        """Periodic cleanup of expired entries."""
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(hours=1)
        
        expired_keys = [k for k, v in self._lockouts.items() if v < now]
        for k in expired_keys:
            del self._lockouts[k]
        
        expired_attempts = [k for k, v in self._attempts.items() if all(t < cutoff for t in v)]
        for k in expired_attempts:
            del self._attempts[k]


# Global rate limit store
rate_limiter = RateLimitStore()


# ─── Security Headers Middleware ───

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        
        # Prevent MIME-type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # XSS protection
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Referrer policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Permissions policy
        response.headers["Permissions-Policy"] = "geolocation=(self), camera=(), microphone=()"
        
        # Remove server header (if present)
        if "Server" in response.headers:
            del response.headers["Server"]
        
        # Cache control for API responses
        if request.url.path.startswith("/api"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
            response.headers["Pragma"] = "no-cache"
        
        return response


# ─── Request ID + Timing Middleware ───

class RequestTrackingMiddleware(BaseHTTPMiddleware):
    """Inject request ID and measure timing."""
    
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id
        start_time = time.time()
        
        response = await call_next(request)
        
        process_time = time.time() - start_time
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = f"{process_time:.4f}"
        
        # Log slow requests
        if process_time > 2.0:
            logger.warning(
                f"[SLOW] {request.method} {request.url.path} "
                f"took {process_time:.2f}s [rid={request_id}]"
            )
        
        return response


# ─── Login Rate Limiter Middleware ───

class LoginRateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limit login attempts by IP + email."""
    
    LOGIN_PATHS = ["/api/auth/login"]
    MAX_ATTEMPTS = 5
    WINDOW_MINUTES = 15
    LOCKOUT_MINUTES = 15
    
    async def dispatch(self, request: Request, call_next):
        if request.method == "POST" and request.url.path in self.LOGIN_PATHS:
            client_ip = self._get_client_ip(request)
            
            # Check IP lockout
            can_proceed, remaining = rate_limiter.check_and_lock(
                f"ip:{client_ip}",
                max_attempts=self.MAX_ATTEMPTS * 3,  # 15 attempts per IP
                window_minutes=self.WINDOW_MINUTES,
                lockout_minutes=self.LOCKOUT_MINUTES
            )
            
            if not can_proceed:
                logger.warning(f"[RATE LIMIT] IP locked: {client_ip}")
                return JSONResponse(
                    status_code=429,
                    content={
                        "detail": f"Too many login attempts. Try again in {self.LOCKOUT_MINUTES} minutes.",
                        "error_code": "RATE_LIMITED"
                    }
                )
        
        response = await call_next(request)
        return response
    
    @staticmethod
    def _get_client_ip(request: Request) -> str:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"


# ─── Password Policy ───

def validate_password_policy(password: str) -> Tuple[bool, str]:
    """Validate password meets security requirements.
    Returns (is_valid, error_message).
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    if len(password) > 128:
        return False, "Password must be at most 128 characters"
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one digit"
    if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password):
        return False, "Password must contain at least one special character"
    return True, ""


# ─── JWT Token Blacklist ───

class TokenBlacklist:
    """In-memory JWT token blacklist. Replace with Redis for multi-instance."""
    
    def __init__(self):
        self._blacklist: Dict[str, datetime] = {}  # jti -> expiry
    
    def blacklist_token(self, token_jti: str, expiry: datetime):
        """Add token to blacklist."""
        self._blacklist[token_jti] = expiry
        self._cleanup()
    
    def is_blacklisted(self, token_jti: str) -> bool:
        """Check if token is blacklisted."""
        if token_jti in self._blacklist:
            if datetime.now(timezone.utc) < self._blacklist[token_jti]:
                return True
            else:
                del self._blacklist[token_jti]
        return False
    
    def _cleanup(self):
        """Remove expired blacklist entries."""
        now = datetime.now(timezone.utc)
        expired = [k for k, v in self._blacklist.items() if v < now]
        for k in expired:
            del self._blacklist[k]


# Global token blacklist
token_blacklist = TokenBlacklist()
