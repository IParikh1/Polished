"""
Stripe billing integration for Pro subscriptions.
$9/month for unlimited resume reviews.
"""

import logging
import os
from typing import Optional, Dict, Any

# Gracefully handle missing stripe dependency
try:
    import stripe
    STRIPE_AVAILABLE = True
except ImportError:
    STRIPE_AVAILABLE = False
    stripe = None
    logging.getLogger(__name__).warning("stripe not installed. Billing disabled.")

logger = logging.getLogger(__name__)

# Initialize Stripe
if STRIPE_AVAILABLE and stripe:
    stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")


class BillingService:
    """Handles Stripe subscriptions for Pro plan."""

    PRICE_PRO = os.getenv("STRIPE_PRICE_PRO", "")  # price_xxx for $9/mo
    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

    def __init__(self):
        if not STRIPE_AVAILABLE:
            logger.warning("Stripe not installed. Billing disabled.")
        elif not stripe.api_key:
            logger.warning("Stripe API key not configured. Billing disabled.")

    def create_checkout_session(
        self,
        user_email: str,
        user_id: str,
        success_url: Optional[str] = None,
        cancel_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create Stripe Checkout session for Pro subscription.
        Returns session URL for redirect.
        """
        if not STRIPE_AVAILABLE or not stripe.api_key or not self.PRICE_PRO:
            raise ValueError("Stripe not configured")

        success_url = success_url or f"{self.FRONTEND_URL}/billing/success"
        cancel_url = cancel_url or f"{self.FRONTEND_URL}/billing/cancel"

        try:
            session = stripe.checkout.Session.create(
                mode="subscription",
                payment_method_types=["card"],
                line_items=[{
                    "price": self.PRICE_PRO,
                    "quantity": 1
                }],
                success_url=success_url + "?session_id={CHECKOUT_SESSION_ID}",
                cancel_url=cancel_url,
                customer_email=user_email,
                metadata={
                    "user_id": user_id
                },
                subscription_data={
                    "metadata": {
                        "user_id": user_id
                    }
                }
            )

            logger.info(f"Created checkout session for user {user_id}")
            return {
                "session_id": session.id,
                "url": session.url
            }

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating checkout: {e}")
            raise

    def create_portal_session(self, customer_id: str) -> Dict[str, Any]:
        """
        Create Stripe Customer Portal session for subscription management.
        """
        if not STRIPE_AVAILABLE or not stripe.api_key:
            raise ValueError("Stripe not configured")

        try:
            session = stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url=f"{self.FRONTEND_URL}/settings"
            )

            return {"url": session.url}

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating portal session: {e}")
            raise

    def get_subscription_status(self, customer_id: str) -> Dict[str, Any]:
        """Get current subscription status for a customer."""
        if not STRIPE_AVAILABLE or not stripe.api_key:
            return {"status": "inactive", "plan": "free"}

        try:
            subscriptions = stripe.Subscription.list(
                customer=customer_id,
                status="active",
                limit=1
            )

            if subscriptions.data:
                sub = subscriptions.data[0]
                return {
                    "status": "active",
                    "plan": "pro",
                    "subscription_id": sub.id,
                    "current_period_end": sub.current_period_end,
                    "cancel_at_period_end": sub.cancel_at_period_end
                }

            return {"status": "inactive", "plan": "free"}

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error getting subscription: {e}")
            return {"status": "error", "plan": "free"}

    def cancel_subscription(self, subscription_id: str) -> bool:
        """Cancel subscription at period end."""
        if not STRIPE_AVAILABLE or not stripe.api_key:
            raise ValueError("Stripe not configured")

        try:
            stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=True
            )
            logger.info(f"Scheduled cancellation for subscription {subscription_id}")
            return True

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error canceling subscription: {e}")
            raise

    def handle_webhook(self, payload: bytes, signature: str) -> Dict[str, Any]:
        """
        Process Stripe webhook events.
        Returns event type and relevant data.
        """
        if not STRIPE_AVAILABLE:
            raise ValueError("Stripe not available")

        webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")
        if not webhook_secret:
            raise ValueError("Webhook secret not configured")

        try:
            event = stripe.Webhook.construct_event(
                payload, signature, webhook_secret
            )
        except stripe.error.SignatureVerificationError:
            logger.error("Invalid webhook signature")
            raise ValueError("Invalid signature")

        event_type = event["type"]
        data = event["data"]["object"]

        # Handle relevant events
        if event_type == "checkout.session.completed":
            user_id = data.get("metadata", {}).get("user_id")
            customer_id = data.get("customer")
            logger.info(f"Checkout completed for user {user_id}, customer {customer_id}")
            return {
                "event": "subscription_created",
                "user_id": user_id,
                "customer_id": customer_id
            }

        elif event_type == "customer.subscription.deleted":
            user_id = data.get("metadata", {}).get("user_id")
            logger.info(f"Subscription deleted for user {user_id}")
            return {
                "event": "subscription_canceled",
                "user_id": user_id
            }

        elif event_type == "invoice.payment_failed":
            customer_id = data.get("customer")
            logger.warning(f"Payment failed for customer {customer_id}")
            return {
                "event": "payment_failed",
                "customer_id": customer_id
            }

        return {"event": event_type, "handled": False}


# Singleton instance
billing_service = BillingService()
