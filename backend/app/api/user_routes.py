"""
User routes for Polished Resume Ranking System.
Handles user profile, admin status, and self-service operations.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional

from ..middleware.auth import get_current_user, AuthenticatedUser
from ..middleware.admin import ADMIN_EMAILS
from ..aws.dynamodb import get_db

router = APIRouter(prefix="/user", tags=["User"])


class UserMeResponse(BaseModel):
    """Response for /me endpoint."""
    user_id: str
    email: Optional[str] = None
    name: Optional[str] = None
    is_admin: bool = False
    subscription_tier: str = "free"
    created: bool = False  # True if user was just created


@router.get("/me", response_model=UserMeResponse)
async def get_current_user_info(
    user: AuthenticatedUser = Depends(get_current_user),
    email: Optional[str] = None,
    name: Optional[str] = None,
):
    """
    Get current user's profile and admin status.

    This endpoint:
    1. Creates the user in DynamoDB if they don't exist
    2. Updates their email if it was missing
    3. Returns their profile including admin status

    Query params:
    - email: User's email from Clerk (frontend should pass this since JWT may not include it)
    - name: User's name from Clerk

    This should be called on app load to ensure user record exists.
    """
    db = get_db()
    created = False

    # Prefer email/name from query params (from Clerk useUser), fallback to JWT token
    user_email = email or user.email
    user_name = name or user.full_name

    print(f"[/me] Request: user_id={user.user_id}, query_email={email}, token_email={user.email}, final_email={user_email}")

    # Get or create user
    existing_user = db.get_user(user.user_id)

    if not existing_user:
        # Create user with info from Clerk
        existing_user = db.create_user({
            "user_id": user.user_id,
            "email": user_email or "",
            "name": user_name or "",
            "subscription_tier": "free",
        })
        created = True
        print(f"[/me] Created new user: {user.user_id}, email={user_email}")
    elif user_email and not existing_user.get("email"):
        # Update email if we have it now but didn't before
        db.update_user(user.user_id, {"email": user_email})
        existing_user["email"] = user_email
        print(f"[/me] Updated user email: {user.user_id}, email={user_email}")
    elif user_email and existing_user.get("email") != user_email:
        # Update email if it changed
        db.update_user(user.user_id, {"email": user_email})
        existing_user["email"] = user_email
        print(f"[/me] Updated user email (changed): {user.user_id}, email={user_email}")

    # Determine admin status
    final_email = user_email or existing_user.get("email")
    is_admin = existing_user.get("is_admin", False)

    # Check if should be admin based on email
    if not is_admin and final_email and final_email.lower() in ADMIN_EMAILS:
        is_admin = True
        db.set_user_admin(user.user_id, True)
        print(f"[/me] Granted admin to user {user.user_id} based on email {final_email}")

    return UserMeResponse(
        user_id=user.user_id,
        email=final_email,
        name=existing_user.get("name") or user_name,
        is_admin=is_admin,
        subscription_tier=existing_user.get("subscription_tier", "free"),
        created=created,
    )


@router.post("/me/sync")
async def sync_user_info(
    user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Sync user info from Clerk to DynamoDB.

    Call this if user updated their profile in Clerk.
    """
    db = get_db()

    updates = {}
    if user.email:
        updates["email"] = user.email
    if user.full_name:
        updates["name"] = user.full_name

    if updates:
        db.update_user(user.user_id, updates)

    return {"synced": True, "updates": list(updates.keys())}
