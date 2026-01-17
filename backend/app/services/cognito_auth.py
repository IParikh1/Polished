"""
AWS Cognito authentication service.
Handles JWT verification and user management.
"""

import logging
import time
import hashlib
import hmac
import base64
from typing import Optional, Dict, Any
from functools import lru_cache

import httpx
from jose import jwt, jwk, JWTError
from jose.utils import base64url_decode
from pydantic import BaseModel

from app.core.config import (
    COGNITO_USER_POOL_ID,
    COGNITO_CLIENT_ID,
    COGNITO_CLIENT_SECRET,
    COGNITO_REGION,
    COGNITO_ISSUER,
    COGNITO_JWKS_URL,
    COGNITO_DOMAIN,
    FRONTEND_URL
)

logger = logging.getLogger(__name__)


class CognitoUser(BaseModel):
    """Authenticated user from Cognito token."""
    sub: str  # Cognito user ID
    email: Optional[str] = None
    email_verified: bool = False
    name: Optional[str] = None
    plan: str = "free"  # Custom attribute: custom:plan
    cognito_groups: list = []


class CognitoAuth:
    """AWS Cognito authentication handler."""

    def __init__(self):
        self.user_pool_id = COGNITO_USER_POOL_ID
        self.client_id = COGNITO_CLIENT_ID
        self.client_secret = COGNITO_CLIENT_SECRET
        self.region = COGNITO_REGION
        self.issuer = COGNITO_ISSUER
        self.jwks_url = COGNITO_JWKS_URL
        self.domain = COGNITO_DOMAIN

        self._jwks_cache: Optional[Dict] = None
        self._jwks_cache_time: float = 0
        self._jwks_cache_ttl: int = 3600  # 1 hour

        if not self.user_pool_id or not self.client_id:
            logger.warning("Cognito not configured. Auth will be disabled.")

    @property
    def is_configured(self) -> bool:
        """Check if Cognito is properly configured."""
        return bool(self.user_pool_id and self.client_id)

    def _get_secret_hash(self, username: str) -> str:
        """Generate secret hash for Cognito API calls (if client secret is configured)."""
        if not self.client_secret:
            return ""

        message = username + self.client_id
        dig = hmac.new(
            self.client_secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).digest()
        return base64.b64encode(dig).decode()

    async def _get_jwks(self) -> Dict:
        """Fetch and cache JWKS from Cognito."""
        now = time.time()

        # Return cached JWKS if still valid
        if self._jwks_cache and (now - self._jwks_cache_time) < self._jwks_cache_ttl:
            return self._jwks_cache

        if not self.jwks_url:
            raise ValueError("Cognito not configured")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.jwks_url)
                response.raise_for_status()
                self._jwks_cache = response.json()
                self._jwks_cache_time = now
                logger.debug("Refreshed Cognito JWKS cache")
                return self._jwks_cache
        except Exception as e:
            logger.error(f"Failed to fetch JWKS: {e}")
            # Return stale cache if available
            if self._jwks_cache:
                return self._jwks_cache
            raise

    def _get_jwks_sync(self) -> Dict:
        """Synchronous JWKS fetch for middleware."""
        now = time.time()

        if self._jwks_cache and (now - self._jwks_cache_time) < self._jwks_cache_ttl:
            return self._jwks_cache

        if not self.jwks_url:
            raise ValueError("Cognito not configured")

        try:
            response = httpx.get(self.jwks_url)
            response.raise_for_status()
            self._jwks_cache = response.json()
            self._jwks_cache_time = now
            return self._jwks_cache
        except Exception as e:
            logger.error(f"Failed to fetch JWKS: {e}")
            if self._jwks_cache:
                return self._jwks_cache
            raise

    async def verify_token(self, token: str) -> Optional[CognitoUser]:
        """
        Verify a Cognito JWT token and return user info.
        Returns None if token is invalid.
        """
        if not self.is_configured:
            logger.warning("Cognito not configured, skipping token verification")
            return None

        try:
            # Get the key ID from the token header
            headers = jwt.get_unverified_headers(token)
            kid = headers.get("kid")

            if not kid:
                logger.warning("No kid in token header")
                return None

            # Get JWKS and find the matching key
            jwks = await self._get_jwks()
            key = None
            for k in jwks.get("keys", []):
                if k.get("kid") == kid:
                    key = k
                    break

            if not key:
                logger.warning(f"Key {kid} not found in JWKS")
                return None

            # Verify and decode the token
            public_key = jwk.construct(key)
            claims = jwt.decode(
                token,
                public_key,
                algorithms=["RS256"],
                audience=self.client_id,
                issuer=self.issuer,
                options={
                    "verify_exp": True,
                    "verify_aud": True,
                    "verify_iss": True
                }
            )

            # Extract user info from claims
            return CognitoUser(
                sub=claims.get("sub"),
                email=claims.get("email"),
                email_verified=claims.get("email_verified", False),
                name=claims.get("name") or claims.get("cognito:username"),
                plan=claims.get("custom:plan", "free"),
                cognito_groups=claims.get("cognito:groups", [])
            )

        except JWTError as e:
            logger.warning(f"JWT verification failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Token verification error: {e}")
            return None

    def verify_token_sync(self, token: str) -> Optional[CognitoUser]:
        """Synchronous token verification for middleware."""
        if not self.is_configured:
            return None

        try:
            headers = jwt.get_unverified_headers(token)
            kid = headers.get("kid")

            if not kid:
                return None

            jwks = self._get_jwks_sync()
            key = None
            for k in jwks.get("keys", []):
                if k.get("kid") == kid:
                    key = k
                    break

            if not key:
                return None

            public_key = jwk.construct(key)
            claims = jwt.decode(
                token,
                public_key,
                algorithms=["RS256"],
                audience=self.client_id,
                issuer=self.issuer,
                options={
                    "verify_exp": True,
                    "verify_aud": True,
                    "verify_iss": True
                }
            )

            return CognitoUser(
                sub=claims.get("sub"),
                email=claims.get("email"),
                email_verified=claims.get("email_verified", False),
                name=claims.get("name") or claims.get("cognito:username"),
                plan=claims.get("custom:plan", "free"),
                cognito_groups=claims.get("cognito:groups", [])
            )

        except Exception as e:
            logger.warning(f"Sync token verification failed: {e}")
            return None

    def get_login_url(self, redirect_uri: Optional[str] = None, state: Optional[str] = None) -> str:
        """Get Cognito hosted UI login URL."""
        if not self.domain:
            raise ValueError("Cognito domain not configured")

        redirect = redirect_uri or f"{FRONTEND_URL}/auth/callback"
        url = (
            f"https://{self.domain}/login"
            f"?client_id={self.client_id}"
            f"&response_type=code"
            f"&scope=email+openid+profile"
            f"&redirect_uri={redirect}"
        )
        if state:
            url += f"&state={state}"
        return url

    def get_logout_url(self, redirect_uri: Optional[str] = None) -> str:
        """Get Cognito logout URL."""
        if not self.domain:
            raise ValueError("Cognito domain not configured")

        redirect = redirect_uri or FRONTEND_URL
        return (
            f"https://{self.domain}/logout"
            f"?client_id={self.client_id}"
            f"&logout_uri={redirect}"
        )

    async def exchange_code_for_tokens(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        """Exchange authorization code for tokens."""
        if not self.domain:
            raise ValueError("Cognito domain not configured")

        token_url = f"https://{self.domain}/oauth2/token"

        data = {
            "grant_type": "authorization_code",
            "client_id": self.client_id,
            "code": code,
            "redirect_uri": redirect_uri
        }

        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        # Add client secret if configured
        if self.client_secret:
            auth = base64.b64encode(
                f"{self.client_id}:{self.client_secret}".encode()
            ).decode()
            headers["Authorization"] = f"Basic {auth}"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(token_url, data=data, headers=headers)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Token exchange failed: {e.response.text}")
            raise ValueError(f"Token exchange failed: {e.response.status_code}")

    async def refresh_tokens(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh access token using refresh token."""
        if not self.domain:
            raise ValueError("Cognito domain not configured")

        token_url = f"https://{self.domain}/oauth2/token"

        data = {
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "refresh_token": refresh_token
        }

        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        if self.client_secret:
            auth = base64.b64encode(
                f"{self.client_id}:{self.client_secret}".encode()
            ).decode()
            headers["Authorization"] = f"Basic {auth}"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(token_url, data=data, headers=headers)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Token refresh failed: {e.response.text}")
            raise ValueError(f"Token refresh failed: {e.response.status_code}")


# Singleton instance
cognito_auth = CognitoAuth()
