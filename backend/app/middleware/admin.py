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
ADMIN_EMAILS = set(
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

    # Also check if email is in admin list
    if not is_admin and user.email:
        is_admin = user.email.lower() in ADMIN_EMAILS
        if is_admin:
            # Auto-grant admin status in database
            db.set_user_admin(user.user_id, True)

    if not is_admin:
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

    # Check email list
    if user.email and user.email.lower() in ADMIN_EMAILS:
        return True

    return False
