"""
Authentication API routes for AWS Cognito.
Handles OAuth flow, token exchange, and user info.
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from app.services.cognito_auth import cognito_auth, CognitoUser
from app.core.auth import require_auth, get_optional_user
from app.core.config import FRONTEND_URL

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])


class TokenResponse(BaseModel):
    """Token response from OAuth flow."""
    access_token: str
    id_token: str
    refresh_token: Optional[str] = None
    token_type: str = "Bearer"
    expires_in: int


class RefreshRequest(BaseModel):
    """Request to refresh tokens."""
    refresh_token: str


class UserInfoResponse(BaseModel):
    """User information response."""
    user_id: str
    email: Optional[str]
    email_verified: bool
    name: Optional[str]
    plan: str
    groups: list


@router.get("/login")
async def login(
    redirect_uri: Optional[str] = Query(None, description="Post-login redirect URI"),
    state: Optional[str] = Query(None, description="State parameter for CSRF protection")
):
    """
    Redirect to Cognito hosted UI for login.
    Frontend should redirect user here to initiate login flow.
    """
    if not cognito_auth.is_configured:
        raise HTTPException(
            status_code=503,
            detail="Authentication not configured"
        )

    try:
        login_url = cognito_auth.get_login_url(redirect_uri, state)
        return RedirectResponse(url=login_url)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/signup")
async def signup(
    redirect_uri: Optional[str] = Query(None, description="Post-signup redirect URI")
):
    """
    Redirect to Cognito hosted UI for signup.
    Uses the same URL as login but Cognito shows signup option.
    """
    if not cognito_auth.is_configured:
        raise HTTPException(
            status_code=503,
            detail="Authentication not configured"
        )

    try:
        # Cognito hosted UI has both login and signup options
        login_url = cognito_auth.get_login_url(redirect_uri)
        return RedirectResponse(url=login_url)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/logout")
async def logout(
    redirect_uri: Optional[str] = Query(None, description="Post-logout redirect URI")
):
    """
    Redirect to Cognito logout URL.
    Clears Cognito session and redirects to frontend.
    """
    if not cognito_auth.is_configured:
        raise HTTPException(
            status_code=503,
            detail="Authentication not configured"
        )

    try:
        logout_url = cognito_auth.get_logout_url(redirect_uri)
        return RedirectResponse(url=logout_url)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/callback", response_model=TokenResponse)
async def auth_callback(
    code: str = Query(..., description="Authorization code from Cognito"),
    state: Optional[str] = Query(None, description="State parameter"),
    redirect_uri: str = Query(f"{FRONTEND_URL}/auth/callback", description="Redirect URI used in login")
):
    """
    Handle OAuth callback from Cognito.
    Exchanges authorization code for tokens.

    Frontend should:
    1. Receive redirect from Cognito with ?code=xxx
    2. Call this endpoint with the code
    3. Store returned tokens (access_token, id_token, refresh_token)
    4. Use access_token in Authorization header for API calls
    """
    if not cognito_auth.is_configured:
        raise HTTPException(
            status_code=503,
            detail="Authentication not configured"
        )

    try:
        tokens = await cognito_auth.exchange_code_for_tokens(code, redirect_uri)

        return TokenResponse(
            access_token=tokens.get("access_token"),
            id_token=tokens.get("id_token"),
            refresh_token=tokens.get("refresh_token"),
            token_type=tokens.get("token_type", "Bearer"),
            expires_in=tokens.get("expires_in", 3600)
        )

    except ValueError as e:
        logger.error(f"Token exchange failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Auth callback error: {e}")
        raise HTTPException(status_code=500, detail="Authentication failed")


@router.post("/refresh", response_model=TokenResponse)
async def refresh_tokens(request: RefreshRequest):
    """
    Refresh access token using refresh token.
    Use when access token expires.
    """
    if not cognito_auth.is_configured:
        raise HTTPException(
            status_code=503,
            detail="Authentication not configured"
        )

    try:
        tokens = await cognito_auth.refresh_tokens(request.refresh_token)

        return TokenResponse(
            access_token=tokens.get("access_token"),
            id_token=tokens.get("id_token"),
            refresh_token=tokens.get("refresh_token"),  # May not be returned
            token_type=tokens.get("token_type", "Bearer"),
            expires_in=tokens.get("expires_in", 3600)
        )

    except ValueError as e:
        logger.error(f"Token refresh failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    except Exception as e:
        logger.error(f"Refresh error: {e}")
        raise HTTPException(status_code=500, detail="Token refresh failed")


@router.get("/me", response_model=UserInfoResponse)
async def get_current_user_info(user: CognitoUser = Depends(require_auth)):
    """
    Get current authenticated user's information.
    Requires valid access token in Authorization header.
    """
    return UserInfoResponse(
        user_id=user.sub,
        email=user.email,
        email_verified=user.email_verified,
        name=user.name,
        plan=user.plan,
        groups=user.cognito_groups
    )


@router.get("/verify")
async def verify_token(user: Optional[CognitoUser] = Depends(get_optional_user)):
    """
    Verify if the current token is valid.
    Returns user info if valid, or unauthenticated status.
    """
    if user:
        return {
            "authenticated": True,
            "user_id": user.sub,
            "email": user.email,
            "plan": user.plan
        }
    return {
        "authenticated": False,
        "user_id": None,
        "email": None,
        "plan": "anonymous"
    }


@router.get("/config")
async def get_auth_config():
    """
    Get public auth configuration for frontend.
    Returns Cognito settings needed for client-side auth.
    """
    if not cognito_auth.is_configured:
        return {
            "configured": False,
            "message": "Authentication not configured"
        }

    return {
        "configured": True,
        "region": cognito_auth.region,
        "userPoolId": cognito_auth.user_pool_id,
        "clientId": cognito_auth.client_id,
        "domain": cognito_auth.domain,
        "loginUrl": f"/api/auth/login",
        "logoutUrl": f"/api/auth/logout",
        "callbackUrl": f"{FRONTEND_URL}/auth/callback"
    }
