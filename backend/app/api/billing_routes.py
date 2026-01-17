"""
Billing API routes for Stripe subscription management.
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Header, Request
from pydantic import BaseModel

from app.services.billing import billing_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/billing", tags=["billing"])


class CheckoutRequest(BaseModel):
    email: str
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None


class PortalRequest(BaseModel):
    customer_id: str


@router.post("/checkout")
async def create_checkout(
    request: CheckoutRequest,
    x_user_id: Optional[str] = Header(None)
):
    """
    Create a Stripe Checkout session for Pro subscription.
    Returns URL to redirect user to Stripe.
    """
    if not x_user_id:
        raise HTTPException(
            status_code=401,
            detail="User ID required for checkout"
        )

    try:
        result = billing_service.create_checkout_session(
            user_email=request.email,
            user_id=x_user_id,
            success_url=request.success_url,
            cancel_url=request.cancel_url
        )
        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Checkout error: {e}")
        raise HTTPException(status_code=500, detail="Failed to create checkout session")


@router.post("/portal")
async def create_portal(request: PortalRequest):
    """
    Create a Stripe Customer Portal session for subscription management.
    Returns URL to redirect user to manage their subscription.
    """
    try:
        result = billing_service.create_portal_session(request.customer_id)
        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Portal error: {e}")
        raise HTTPException(status_code=500, detail="Failed to create portal session")


@router.get("/status/{customer_id}")
async def get_subscription_status(customer_id: str):
    """Get current subscription status."""
    return billing_service.get_subscription_status(customer_id)


@router.post("/webhook")
async def stripe_webhook(request: Request):
    """
    Handle Stripe webhook events.
    Must be configured in Stripe Dashboard.
    """
    payload = await request.body()
    signature = request.headers.get("stripe-signature", "")

    try:
        result = billing_service.handle_webhook(payload, signature)

        # Handle events that require database updates
        if result.get("event") == "subscription_created":
            # TODO: Update user plan in database
            logger.info(f"User {result.get('user_id')} upgraded to Pro")

        elif result.get("event") == "subscription_canceled":
            # TODO: Update user plan in database
            logger.info(f"User {result.get('user_id')} subscription canceled")

        return {"status": "ok", "event": result.get("event")}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")
