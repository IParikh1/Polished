"""
Stripe subscription routes for Polished Resume Ranking System.
Handles checkout, webhooks, and subscription management.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Header
from typing import Optional
import os

from ..middleware.auth import get_current_user, AuthenticatedUser
from ..services.subscription_service import get_subscription_service
from ..models.subscription_schemas import (
    CheckoutSessionRequest,
    CheckoutSessionResponse,
    PortalSessionRequest,
    PortalSessionResponse,
    SubscriptionResponse,
    FeatureAccessResponse,
    ProFeature,
    FEATURE_INFO,
)

router = APIRouter(prefix="/subscription", tags=["Subscription"])


@router.get("/status", response_model=SubscriptionResponse)
async def get_subscription_status(
    user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Get current user's subscription status.

    Returns tier, features, and limits for the authenticated user.
    """
    service = get_subscription_service()
    subscription = service.get_user_subscription(
        user_id=user.user_id,
        email=user.email or "",
        name=user.full_name
    )

    # Build response
    return SubscriptionResponse(
        tier=subscription["tier"],
        status=subscription.get("status"),
        is_pro=subscription["is_pro"],
        features=subscription["features"],
        limits=subscription["limits"],
        upgrade_url="/pricing" if not subscription["is_pro"] else None,
        manage_url="/subscription/portal" if subscription["is_pro"] else None,
    )


@router.get("/features")
async def get_all_features(
    user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Get access status for all Pro features.

    Returns a list of all features with their access status for the user.
    """
    service = get_subscription_service()
    features = service.get_all_features_status(user.user_id)

    return {
        "features": features,
        "user_tier": service.get_user_subscription(user.user_id)["tier"],
    }


@router.get("/features/{feature}", response_model=FeatureAccessResponse)
async def check_feature_access(
    feature: str,
    user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Check if user has access to a specific Pro feature.

    Returns access status and upgrade information if needed.
    """
    service = get_subscription_service()
    result = service.check_feature_access(user.user_id, feature)

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return FeatureAccessResponse(**result)


@router.get("/config")
async def get_stripe_config():
    """
    Get Stripe configuration for frontend.

    Returns publishable key and price IDs (no secrets).
    """
    return {
        "publishable_key": os.getenv("STRIPE_PUBLISHABLE_KEY", ""),
        "pro_price_id": os.getenv("STRIPE_PRO_PRICE_ID", ""),
        "stripe_configured": bool(os.getenv("STRIPE_SECRET_KEY")),
        "prices": {
            "pro": {
                "monthly": 29,
                "price_id": os.getenv("STRIPE_PRO_PRICE_ID", ""),
            }
        }
    }


@router.post("/checkout", response_model=CheckoutSessionResponse)
async def create_checkout_session(
    request: CheckoutSessionRequest,
    user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Create a Stripe checkout session for Pro subscription.

    Returns a URL to redirect the user to Stripe's checkout page.
    """
    service = get_subscription_service()

    if not service.is_available():
        raise HTTPException(
            status_code=503,
            detail="Payment processing is not configured"
        )

    try:
        result = service.create_checkout_session(
            user_id=user.user_id,
            email=user.email or "",
            price_id=request.price_id,
            success_url=request.success_url,
            cancel_url=request.cancel_url,
        )
        return CheckoutSessionResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/portal", response_model=PortalSessionResponse)
async def create_portal_session(
    request: PortalSessionRequest,
    user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Create a Stripe customer portal session.

    Allows Pro users to manage their subscription (cancel, update payment, etc.).
    """
    service = get_subscription_service()

    if not service.is_available():
        raise HTTPException(
            status_code=503,
            detail="Payment processing is not configured"
        )

    try:
        result = service.create_portal_session(
            user_id=user.user_id,
            return_url=request.return_url,
        )
        return PortalSessionResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="Stripe-Signature")
):
    """
    Handle Stripe webhook events.

    This endpoint receives events from Stripe about subscription changes.
    Must be configured in Stripe dashboard to send:
    - checkout.session.completed
    - customer.subscription.updated
    - customer.subscription.deleted
    - invoice.payment_failed
    """
    service = get_subscription_service()

    if not service.is_available():
        raise HTTPException(
            status_code=503,
            detail="Payment processing is not configured"
        )

    if not stripe_signature:
        raise HTTPException(status_code=400, detail="Missing Stripe signature")

    payload = await request.body()

    try:
        result = service.handle_webhook(payload, stripe_signature)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/pricing")
async def get_pricing_info():
    """
    Get pricing information for display on pricing page.

    Returns all tiers with their features and prices.
    """
    return {
        "tiers": [
            {
                "id": "free",
                "name": "Free",
                "price": 0,
                "billing": "forever",
                "description": "Perfect for trying out Polished",
                "features": [
                    "5 batches per month",
                    "50 resumes per batch",
                    "Basic scoring",
                    "Role-specific optimization",
                    "CSV export",
                ],
                "limitations": [
                    "No JD Matching",
                    "No Deep Analysis",
                    "No Resume Writing",
                    "No PDF/DOCX export",
                ],
                "cta": "Current Plan",
                "highlighted": False,
            },
            {
                "id": "pro",
                "name": "Pro",
                "price": 29,
                "billing": "per month",
                "description": "For power users and recruiting teams",
                "features": [
                    "100 batches per month",
                    "500 resumes per batch",
                    "All Free features",
                    "JD Matching",
                    "Deep Analysis",
                    "Resume Writing",
                    "PDF/DOCX export",
                    "Priority processing",
                ],
                "limitations": [],
                "cta": "Upgrade to Pro",
                "highlighted": True,
                "price_id": os.getenv("STRIPE_PRO_PRICE_ID", ""),
            },
            {
                "id": "enterprise",
                "name": "Enterprise",
                "price": None,
                "billing": "custom",
                "description": "For large teams with custom needs",
                "features": [
                    "Unlimited batches",
                    "Unlimited resumes",
                    "All Pro features",
                    "Custom scoring rules",
                    "SSO/SAML",
                    "Dedicated support",
                    "SLA guarantee",
                    "API access",
                ],
                "limitations": [],
                "cta": "Contact Sales",
                "highlighted": False,
            },
        ],
        "faq": [
            {
                "question": "What payment methods do you accept?",
                "answer": "We accept all major credit cards (Visa, Mastercard, American Express) through our secure payment processor, Stripe.",
            },
            {
                "question": "Can I cancel my subscription anytime?",
                "answer": "Yes, you can cancel your Pro subscription at any time. You'll continue to have access to Pro features until the end of your billing period.",
            },
            {
                "question": "Do you offer refunds?",
                "answer": "We offer a 7-day money-back guarantee. If you're not satisfied with Pro, contact us within 7 days for a full refund.",
            },
            {
                "question": "What happens to my data if I downgrade?",
                "answer": "Your data is safe! You'll still have access to all your batches and resumes, but Pro features will be unavailable until you upgrade again.",
            },
        ],
    }
