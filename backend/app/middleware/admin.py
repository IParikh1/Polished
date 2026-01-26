"""
Admin middleware for Polished API.
Provides admin-only access control.
"""

from fastapi import Depends, HTTPException, status
from typing import Optional
from .auth import AuthenticatedUser, get_current_user
from ..aws.dynamodb import get_db

# Hardcoded admin user IDs (can be configured via environment)
import os

# Admin emails that should automatically have admin access
# Hardcoded admin emails (always have access)
_HARDCODED_ADMINS = {"ishanparikh@me.com"}

# Combine with environment variable
ADMIN_EMAILS = _HARDCODED_ADMINS | set(
    email.strip().lower()
    for email in os.getenv("ADMIN_EMAILS", "").split(",")
    if email.strip()
)


async def get_current_admin(
    user: AuthenticatedUser = Depends(get_current_user)
) -> AuthenticatedUser:
    """
    Dependency to verify the current user is an admin.
    Raises 403 if not an admin.

    Usage:
        @router.get("/admin-only")
        async def admin_endpoint(admin: AuthenticatedUser = Depends(get_current_admin)):
            return {"admin_id": admin.user_id}
    """
    db = get_db()

    # Check if user is admin in database
    is_admin = db.is_user_admin(user.user_id)

    if not is_admin:
        # Get email - from token or from DynamoDB
        email = user.email
        print(f"[Admin Check] user_id={user.user_id}, token_email={user.email}")

        if not email:
            # Clerk tokens may not include email - look it up from DynamoDB
            user_data = db.get_user(user.user_id)
            if user_data:
                email = user_data.get("email")
                print(f"[Admin Check] Found email in DynamoDB: {email}")

        # Check if email is in admin list
        print(f"[Admin Check] Checking email={email} against ADMIN_EMAILS={ADMIN_EMAILS}")
        if email and email.lower() in ADMIN_EMAILS:
            is_admin = True
            # Auto-grant admin status in database
            db.set_user_admin(user.user_id, True)
            print(f"[Admin Check] Granted admin to user {user.user_id}")

    if not is_admin:
        print(f"[Admin Check] Access denied for user {user.user_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    return user


def is_admin_user(user: AuthenticatedUser) -> bool:
    """Check if a user has admin privileges without raising."""
    db = get_db()

    # Check database first
    if db.is_user_admin(user.user_id):
        return True

    # Get email - from token or from DynamoDB
    email = user.email
    if not email:
        user_data = db.get_user(user.user_id)
        if user_data:
            email = user_data.get("email")

    # Check email list
    if email and email.lower() in ADMIN_EMAILS:
        return True

    return False
