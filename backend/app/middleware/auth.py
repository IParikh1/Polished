"""
Authentication middleware for Polished API.
Verifies Clerk JWT tokens and extracts user information.
"""

import os
import jwt
from jwt import PyJWKClient
from typing import Optional
from dataclasses import dataclass
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# Clerk configuration
CLERK_PUBLISHABLE_KEY = os.getenv("CLERK_PUBLISHABLE_KEY", "")
CLERK_SECRET_KEY = os.getenv("CLERK_SECRET_KEY", "")
# Clerk issuer URL - can be set directly or will be extracted from token
CLERK_ISSUER_URL = os.getenv("CLERK_ISSUER_URL", "")


def get_trusted_issuer() -> str:
    """
    Get the trusted Clerk issuer URL. Tokens whose 'iss' claim does not match
    this value are rejected. Never derived from the (attacker-controlled) token.
    """
    # If issuer URL is explicitly set, use it
    if CLERK_ISSUER_URL:
        return CLERK_ISSUER_URL.rstrip("/")

    # Fallback: construct from publishable key (server-side config, not the token).
    # The part after pk_test_/pk_live_ is the base64-encoded Clerk frontend API domain.
    if CLERK_PUBLISHABLE_KEY:
        try:
            import base64
            if CLERK_PUBLISHABLE_KEY.startswith("pk_test_"):
                encoded = CLERK_PUBLISHABLE_KEY.replace("pk_test_", "")
            elif CLERK_PUBLISHABLE_KEY.startswith("pk_live_"):
                encoded = CLERK_PUBLISHABLE_KEY.replace("pk_live_", "")
            else:
                encoded = ""

            if encoded:
                # Add padding if needed
                padding = 4 - len(encoded) % 4
                if padding != 4:
                    encoded += "=" * padding
                decoded = base64.b64decode(encoded).decode("utf-8").strip().rstrip("$")
                # Format: clerk.xxx.xxx or xxx.clerk.accounts.dev
                return f"https://{decoded}"
        except Exception as e:
            print(f"Failed to decode Clerk publishable key: {e}")

    # No trusted issuer configured - verification must fail closed
    return ""


def get_clerk_jwks_url() -> str:
    """Get the JWKS URL for Clerk token verification (from the trusted issuer only)."""
    issuer = get_trusted_issuer()
    return f"{issuer}/.well-known/jwks.json" if issuer else ""


def _is_production() -> bool:
    return os.getenv("ENVIRONMENT", "development").lower() == "production"


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


# Cache for JWKS clients - keyed by URL to support multiple issuers
_jwks_clients: dict[str, PyJWKClient] = {}


def get_jwks_client(jwks_url: str) -> PyJWKClient:
    """
    Get or create a cached JWKS client for the given URL.
    Caches clients per URL to avoid repeated network calls.
    """
    if jwks_url not in _jwks_clients:
        _jwks_clients[jwks_url] = PyJWKClient(jwks_url)
    return _jwks_clients[jwks_url]


def verify_clerk_token(token: str) -> Optional[dict]:
    """
    Verify a Clerk JWT token and return the decoded payload.

    Returns:
        Decoded token payload if valid, None otherwise
    """
    try:
        # Only ever fetch keys from the configured/derived issuer - never from
        # the token's own 'iss' claim (that would let an attacker point us at
        # their own JWKS and mint arbitrary identities).
        trusted_issuer = get_trusted_issuer()
        jwks_url = get_clerk_jwks_url()

        if not trusted_issuer or not jwks_url:
            print("No trusted Clerk issuer configured (set CLERK_ISSUER_URL) - rejecting token")
            return None

        # Get cached JWKS client for this URL
        jwks_client = get_jwks_client(jwks_url)
        signing_key = jwks_client.get_signing_key_from_jwt(token)

        # Decode and verify the token, pinning the issuer
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            issuer=trusted_issuer,
            options={
                "verify_signature": True,
                "verify_exp": True,
                "verify_iss": True,
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
    # Check for development/bypass mode (never honored in production)
    if os.getenv("AUTH_BYPASS", "").lower() == "true" and not _is_production():
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
    # Check for development/bypass mode (never honored in production)
    if os.getenv("AUTH_BYPASS", "").lower() == "true" and not _is_production():
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
