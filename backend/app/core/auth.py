"""
Authentication middleware and dependencies for FastAPI.
Uses AWS Cognito for JWT verification.
"""

import logging
from typing import Optional

from fastapi import Depends, HTTPException, Header, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.services.cognito_auth import cognito_auth, CognitoUser
from app.services.rate_limiter import PlanType

logger = logging.getLogger(__name__)

# HTTP Bearer token extractor
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    authorization: Optional[str] = Header(None)
) -> Optional[CognitoUser]:
    """
    Extract and verify JWT token from Authorization header.
    Returns CognitoUser if valid, None if no token provided.
    Raises HTTPException if token is invalid.
    """
    token = None

    # Try HTTPBearer first, then raw header
    if credentials:
        token = credentials.credentials
    elif authorization and authorization.startswith("Bearer "):
        token = authorization[7:]

    if not token:
        return None

    # Verify token with Cognito
    user = await cognito_auth.verify_token(token)

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )

    return user


async def require_auth(
    user: Optional[CognitoUser] = Depends(get_current_user)
) -> CognitoUser:
    """
    Require authentication. Raises 401 if not authenticated.
    Use as dependency for protected routes.
    """
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return user


async def require_pro(
    user: CognitoUser = Depends(require_auth)
) -> CognitoUser:
    """
    Require Pro plan. Raises 403 if not Pro.
    Use as dependency for Pro-only features.
    """
    if user.plan not in ["pro", "enterprise"]:
        raise HTTPException(
            status_code=403,
            detail="Pro subscription required for this feature"
        )
    return user


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    authorization: Optional[str] = Header(None)
) -> Optional[CognitoUser]:
    """
    Get user if authenticated, None otherwise.
    Does not raise exceptions for missing/invalid tokens.
    Use for routes that work for both authenticated and anonymous users.
    """
    token = None

    if credentials:
        token = credentials.credentials
    elif authorization and authorization.startswith("Bearer "):
        token = authorization[7:]

    if not token:
        return None

    # Verify token, but don't raise on failure
    return await cognito_auth.verify_token(token)


def get_user_id_from_auth(user: Optional[CognitoUser], fallback_id: Optional[str] = None) -> str:
    """
    Get user ID for rate limiting.
    Uses Cognito sub if authenticated, otherwise falls back to provided ID.
    """
    if user:
        return user.sub
    return fallback_id or "anonymous"


def get_plan_from_auth(user: Optional[CognitoUser]) -> PlanType:
    """
    Get user's plan from Cognito user.
    """
    if not user:
        return PlanType.ANONYMOUS

    plan_map = {
        "free": PlanType.FREE,
        "pro": PlanType.PRO,
        "enterprise": PlanType.ENTERPRISE
    }
    return plan_map.get(user.plan, PlanType.FREE)


class AuthContext:
    """
    Context object containing authentication info.
    Useful for routes that need both user and plan info.
    """
    def __init__(self, user: Optional[CognitoUser], session_id: Optional[str] = None):
        self.user = user
        self.session_id = session_id
        self.user_id = get_user_id_from_auth(user, session_id)
        self.plan = get_plan_from_auth(user)
        self.is_authenticated = user is not None
        self.is_pro = user is not None and user.plan in ["pro", "enterprise"]


async def get_auth_context(
    user: Optional[CognitoUser] = Depends(get_optional_user),
    x_session_id: Optional[str] = Header(None)
) -> AuthContext:
    """
    Get full authentication context for a request.
    Works for both authenticated and anonymous users.
    """
    return AuthContext(user, x_session_id)
