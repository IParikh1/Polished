"""
Authentication middleware for Polished API.
Verifies Clerk JWT tokens and extracts user information.
"""

import os
import httpx
import jwt
from jwt import PyJWKClient
from typing import Optional
from dataclasses import dataclass
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# Clerk configuration
CLERK_PUBLISHABLE_KEY = os.getenv("CLERK_PUBLISHABLE_KEY", "")
CLERK_SECRET_KEY = os.getenv("CLERK_SECRET_KEY", "")

# Extract Clerk instance ID from publishable key (pk_live_xxx or pk_test_xxx)
# The JWKS URL uses the Clerk frontend API domain
def get_clerk_jwks_url() -> str:
    """Get the JWKS URL for Clerk token verification."""
    if CLERK_PUBLISHABLE_KEY.startswith("pk_test_"):
        # Test/development instance
        instance_id = CLERK_PUBLISHABLE_KEY.replace("pk_test_", "")
    elif CLERK_PUBLISHABLE_KEY.startswith("pk_live_"):
        # Production instance
        instance_id = CLERK_PUBLISHABLE_KEY.replace("pk_live_", "")
    else:
        instance_id = ""

    # Clerk JWKS endpoint
    return f"https://{instance_id}.clerk.accounts.dev/.well-known/jwks.json"


# Security scheme for Bearer tokens
security = HTTPBearer(auto_error=False)


@dataclass
class AuthenticatedUser:
    """Represents an authenticated user from Clerk."""
    user_id: str
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    image_url: Optional[str] = None

    @property
    def full_name(self) -> str:
        """Get the user's full name."""
        parts = [self.first_name, self.last_name]
        return " ".join(p for p in parts if p) or "Unknown User"


# Cache for JWKS client
_jwks_client: Optional[PyJWKClient] = None


def get_jwks_client() -> PyJWKClient:
    """Get or create the JWKS client for token verification."""
    global _jwks_client
    if _jwks_client is None:
        jwks_url = get_clerk_jwks_url()
        _jwks_client = PyJWKClient(jwks_url)
    return _jwks_client


def verify_clerk_token(token: str) -> Optional[dict]:
    """
    Verify a Clerk JWT token and return the decoded payload.

    Returns:
        Decoded token payload if valid, None otherwise
    """
    try:
        # Get the signing key from Clerk's JWKS
        jwks_client = get_jwks_client()
        signing_key = jwks_client.get_signing_key_from_jwt(token)

        # Decode and verify the token
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            options={
                "verify_signature": True,
                "verify_exp": True,
                "verify_aud": False,  # Clerk doesn't use audience
            }
        )

        return payload
    except jwt.ExpiredSignatureError:
        print("Token has expired")
        return None
    except jwt.InvalidTokenError as e:
        print(f"Invalid token: {e}")
        return None
    except Exception as e:
        print(f"Token verification error: {e}")
        return None


def extract_user_from_token(payload: dict) -> AuthenticatedUser:
    """Extract user information from a verified token payload."""
    # Clerk token structure
    user_id = payload.get("sub", "")

    # Additional claims (may vary based on Clerk configuration)
    email = payload.get("email")
    first_name = payload.get("first_name")
    last_name = payload.get("last_name")
    image_url = payload.get("image_url")

    return AuthenticatedUser(
        user_id=user_id,
        email=email,
        first_name=first_name,
        last_name=last_name,
        image_url=image_url,
    )


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> AuthenticatedUser:
    """
    Dependency to get the current authenticated user.
    Raises 401 if not authenticated.

    Usage:
        @router.get("/protected")
        async def protected_endpoint(user: AuthenticatedUser = Depends(get_current_user)):
            return {"user_id": user.user_id}
    """
    # Check for development/bypass mode
    if os.getenv("AUTH_BYPASS", "").lower() == "true":
        return AuthenticatedUser(
            user_id="dev-user-001",
            email="dev@example.com",
            first_name="Dev",
            last_name="User",
        )

    # Check if credentials provided
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify the token
    token = credentials.credentials
    payload = verify_clerk_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return extract_user_from_token(payload)


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[AuthenticatedUser]:
    """
    Dependency to get the current user if authenticated, None otherwise.
    Does not raise an error if not authenticated.

    Usage:
        @router.get("/public-or-private")
        async def endpoint(user: Optional[AuthenticatedUser] = Depends(get_optional_user)):
            if user:
                return {"user_id": user.user_id}
            return {"message": "anonymous access"}
    """
    # Check for development/bypass mode
    if os.getenv("AUTH_BYPASS", "").lower() == "true":
        return AuthenticatedUser(
            user_id="dev-user-001",
            email="dev@example.com",
            first_name="Dev",
            last_name="User",
        )

    if credentials is None:
        return None

    token = credentials.credentials
    payload = verify_clerk_token(token)

    if payload is None:
        return None

    return extract_user_from_token(payload)
