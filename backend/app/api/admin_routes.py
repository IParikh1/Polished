"""
Admin API routes for Polished Resume Ranking System.
Provides admin-only endpoints for user management and analytics.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional
from datetime import datetime

from ..middleware.auth import AuthenticatedUser
from ..middleware.admin import get_current_admin
from ..aws.dynamodb import get_db
from ..models.subscription_schemas import (
    AdminUserResponse,
    AdminUserListResponse,
    AdminStatsResponse,
    UserUsage,
    UserCost,
    SubscriptionTier,
    SubscriptionStatus,
)
from ..services.premium_gate import FEATURE_PRICING, PremiumFeature

router = APIRouter(prefix="/admin", tags=["admin"])


# Cost per unit for services (simplified pricing)
SERVICE_COSTS = {
    "batches_created": 0.0,  # Included in subscription
    "resumes_processed": 0.01,  # $0.01 per resume
    "exports_count": 0.05,  # $0.05 per export
    "jd_matches": 0.10,  # $0.10 per JD match
    "resume_writes": 2.00,  # $2.00 per resume write
    "deep_analyses": 0.50,  # $0.50 per deep analysis
}


def calculate_user_cost(usage: dict) -> UserCost:
    """Calculate cost from usage metrics."""
    return UserCost(
        batches_cost=usage.get("batches_created", 0) * SERVICE_COSTS["batches_created"],
        resumes_cost=usage.get("resumes_processed", 0) * SERVICE_COSTS["resumes_processed"],
        exports_cost=usage.get("exports_count", 0) * SERVICE_COSTS["exports_count"],
        jd_matches_cost=usage.get("jd_matches", 0) * SERVICE_COSTS["jd_matches"],
        resume_writes_cost=usage.get("resume_writes", 0) * SERVICE_COSTS["resume_writes"],
        deep_analyses_cost=usage.get("deep_analyses", 0) * SERVICE_COSTS["deep_analyses"],
        total_cost=(
            usage.get("batches_created", 0) * SERVICE_COSTS["batches_created"] +
            usage.get("resumes_processed", 0) * SERVICE_COSTS["resumes_processed"] +
            usage.get("exports_count", 0) * SERVICE_COSTS["exports_count"] +
            usage.get("jd_matches", 0) * SERVICE_COSTS["jd_matches"] +
            usage.get("resume_writes", 0) * SERVICE_COSTS["resume_writes"] +
            usage.get("deep_analyses", 0) * SERVICE_COSTS["deep_analyses"]
        )
    )


@router.get("/stats", response_model=AdminStatsResponse)
async def get_admin_stats(
    admin: AuthenticatedUser = Depends(get_current_admin)
):
    """Get aggregate statistics for the admin dashboard."""
    db = get_db()
    stats = db.get_admin_stats()

    return AdminStatsResponse(
        total_users=stats["total_users"],
        users_by_tier=stats["users_by_tier"],
        users_by_status=stats["users_by_status"],
        total_batches=stats["total_batches"],
        total_resumes=stats["total_resumes"],
        total_revenue=stats["total_revenue"],
        period=stats["period"],
    )


@router.get("/users", response_model=AdminUserListResponse)
async def list_users(
    limit: int = 50,
    offset: int = 0,
    tier: Optional[str] = None,
    admin: AuthenticatedUser = Depends(get_current_admin)
):
    """List all users with their subscription and usage data."""
    db = get_db()
    users_data, total = db.list_all_users(limit=limit, offset=offset)

    # Get current period for usage
    period = datetime.utcnow().strftime("%Y-%m")

    users = []
    for user_data in users_data:
        # Filter by tier if specified
        user_tier = user_data.get("subscription_tier", "free")
        if tier and user_tier != tier:
            continue

        # Get usage for this user
        usage_data = db.get_user_usage(user_data["user_id"], period)
        usage = None
        cost = None

        if usage_data:
            usage = UserUsage(
                user_id=usage_data["user_id"],
                period=usage_data.get("period", period),
                batches_created=usage_data.get("batches_created", 0),
                resumes_processed=usage_data.get("resumes_processed", 0),
                exports_count=usage_data.get("exports_count", 0),
                jd_matches=usage_data.get("jd_matches", 0),
                resume_writes=usage_data.get("resume_writes", 0),
                deep_analyses=usage_data.get("deep_analyses", 0),
                updated_at=usage_data.get("updated_at", datetime.utcnow().isoformat()),
            )
            cost = calculate_user_cost(usage_data)

        # Parse subscription status
        status_str = user_data.get("subscription_status")
        subscription_status = None
        if status_str:
            try:
                subscription_status = SubscriptionStatus(status_str)
            except ValueError:
                pass

        users.append(AdminUserResponse(
            user_id=user_data["user_id"],
            email=user_data.get("email", ""),
            name=user_data.get("name"),
            subscription_tier=SubscriptionTier(user_tier),
            subscription_status=subscription_status,
            is_admin=user_data.get("is_admin", False),
            stripe_customer_id=user_data.get("stripe_customer_id"),
            created_at=user_data.get("created_at", ""),
            updated_at=user_data.get("updated_at", ""),
            usage=usage,
            cost=cost,
        ))

    return AdminUserListResponse(
        users=users,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/users/{user_id}", response_model=AdminUserResponse)
async def get_user_details(
    user_id: str,
    admin: AuthenticatedUser = Depends(get_current_admin)
):
    """Get detailed information about a specific user."""
    db = get_db()
    user_data = db.get_user(user_id)

    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Get usage
    period = datetime.utcnow().strftime("%Y-%m")
    usage_data = db.get_user_usage(user_id, period)

    usage = None
    cost = None
    if usage_data:
        usage = UserUsage(
            user_id=usage_data["user_id"],
            period=usage_data.get("period", period),
            batches_created=usage_data.get("batches_created", 0),
            resumes_processed=usage_data.get("resumes_processed", 0),
            exports_count=usage_data.get("exports_count", 0),
            jd_matches=usage_data.get("jd_matches", 0),
            resume_writes=usage_data.get("resume_writes", 0),
            deep_analyses=usage_data.get("deep_analyses", 0),
            updated_at=usage_data.get("updated_at", datetime.utcnow().isoformat()),
        )
        cost = calculate_user_cost(usage_data)

    # Parse subscription status
    status_str = user_data.get("subscription_status")
    subscription_status = None
    if status_str:
        try:
            subscription_status = SubscriptionStatus(status_str)
        except ValueError:
            pass

    return AdminUserResponse(
        user_id=user_data["user_id"],
        email=user_data.get("email", ""),
        name=user_data.get("name"),
        subscription_tier=SubscriptionTier(user_data.get("subscription_tier", "free")),
        subscription_status=subscription_status,
        is_admin=user_data.get("is_admin", False),
        stripe_customer_id=user_data.get("stripe_customer_id"),
        created_at=user_data.get("created_at", ""),
        updated_at=user_data.get("updated_at", ""),
        usage=usage,
        cost=cost,
    )


@router.post("/users/{user_id}/admin")
async def set_user_admin_status(
    user_id: str,
    is_admin: bool = True,
    admin: AuthenticatedUser = Depends(get_current_admin)
):
    """Grant or revoke admin status for a user."""
    db = get_db()

    # Verify user exists
    user = db.get_user(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Don't allow removing own admin status
    if user_id == admin.user_id and not is_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove your own admin status"
        )

    success = db.set_user_admin(user_id, is_admin)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update admin status"
        )

    return {
        "message": f"Admin status {'granted' if is_admin else 'revoked'} for user {user_id}",
        "user_id": user_id,
        "is_admin": is_admin,
    }


@router.post("/users/{user_id}/tier")
async def set_user_tier(
    user_id: str,
    tier: str,
    admin: AuthenticatedUser = Depends(get_current_admin)
):
    """Manually set a user's subscription tier."""
    db = get_db()

    # Validate tier
    try:
        subscription_tier = SubscriptionTier(tier)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid tier: {tier}. Must be one of: free, pro, enterprise"
        )

    # Verify user exists
    user = db.get_user(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    success = db.update_user_subscription(user_id, tier)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update subscription tier"
        )

    return {
        "message": f"Subscription tier updated to {tier} for user {user_id}",
        "user_id": user_id,
        "tier": tier,
    }


@router.get("/usage")
async def get_all_usage(
    period: Optional[str] = None,
    admin: AuthenticatedUser = Depends(get_current_admin)
):
    """Get usage data for all users for a period."""
    db = get_db()

    if not period:
        period = datetime.utcnow().strftime("%Y-%m")

    usage_data = db.get_all_usage_for_period(period)

    # Calculate totals
    totals = {
        "batches_created": 0,
        "resumes_processed": 0,
        "exports_count": 0,
        "jd_matches": 0,
        "resume_writes": 0,
        "deep_analyses": 0,
    }

    for usage in usage_data:
        for key in totals:
            totals[key] += usage.get(key, 0)

    total_cost = calculate_user_cost(totals)

    return {
        "period": period,
        "user_count": len(usage_data),
        "usage_by_user": usage_data,
        "totals": totals,
        "total_cost": total_cost,
    }


@router.get("/service-costs")
async def get_service_costs(
    admin: AuthenticatedUser = Depends(get_current_admin)
):
    """Get the current service cost configuration."""
    return {
        "costs_per_unit": SERVICE_COSTS,
        "description": {
            "batches_created": "Cost per batch created",
            "resumes_processed": "Cost per resume processed",
            "exports_count": "Cost per export",
            "jd_matches": "Cost per JD matching operation",
            "resume_writes": "Cost per AI resume write",
            "deep_analyses": "Cost per deep analysis",
        }
    }
