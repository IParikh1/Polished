"""
Subscription Service for Polished Resume Ranking System.
Handles Stripe integration and subscription management.
"""

import os
from typing import Optional, Dict, Any, List
from datetime import datetime

from ..aws.dynamodb import get_db
from ..models.subscription_schemas import (
    SubscriptionTier,
    SubscriptionStatus,
    ProFeature,
    TIER_FEATURES,
    TIER_LIMITS,
    FEATURE_INFO,
)

# Stripe configuration
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
STRIPE_PRO_PRICE_ID = os.getenv("STRIPE_PRO_PRICE_ID", "price_pro_monthly")

# Try to import stripe
try:
    import stripe
    stripe.api_key = STRIPE_SECRET_KEY
    STRIPE_AVAILABLE = bool(STRIPE_SECRET_KEY)
except ImportError:
    stripe = None
    STRIPE_AVAILABLE = False


class SubscriptionService:
    """Service for managing user subscriptions with Stripe."""

    def __init__(self):
        self.db = get_db()

    def is_available(self) -> bool:
        """Check if Stripe integration is available."""
        return STRIPE_AVAILABLE and stripe is not None

    # ==================== User Subscription ====================

    def get_user_subscription(self, user_id: str, email: str = "", name: str = "") -> Dict[str, Any]:
        """
        Get user's subscription status.
        Creates a free tier user if they don't exist.
        """
        user = self.db.get_or_create_user(user_id, email, name)
        tier = SubscriptionTier(user.get("subscription_tier", "free"))

        return {
            "user_id": user_id,
            "tier": tier.value,
            "status": user.get("subscription_status"),
            "is_pro": tier in [SubscriptionTier.PRO, SubscriptionTier.ENTERPRISE],
            "features": [f.value for f in TIER_FEATURES.get(tier, set())],
            "limits": TIER_LIMITS[tier].model_dump(),
            "stripe_customer_id": user.get("stripe_customer_id"),
            "stripe_subscription_id": user.get("stripe_subscription_id"),
        }

    def has_feature(self, user_id: str, feature: ProFeature) -> bool:
        """Check if user has access to a specific feature."""
        # Check for bypass mode
        if os.getenv("PREMIUM_BYPASS", "").lower() == "true":
            return True

        user = self.db.get_user(user_id)
        if not user:
            return False

        tier = SubscriptionTier(user.get("subscription_tier", "free"))
        return feature in TIER_FEATURES.get(tier, set())

    def check_feature_access(self, user_id: str, feature: str) -> Dict[str, Any]:
        """Check if user can access a feature and return details."""
        try:
            pro_feature = ProFeature(feature)
        except ValueError:
            return {
                "feature": feature,
                "has_access": False,
                "error": "Invalid feature name",
            }

        user = self.db.get_user(user_id)
        current_tier = SubscriptionTier(user.get("subscription_tier", "free") if user else "free")

        # Find minimum required tier for this feature
        required_tier = SubscriptionTier.PRO  # Default
        for tier, features in TIER_FEATURES.items():
            if pro_feature in features:
                required_tier = tier
                break

        has_access = pro_feature in TIER_FEATURES.get(current_tier, set())

        # Check for bypass mode
        if os.getenv("PREMIUM_BYPASS", "").lower() == "true":
            has_access = True

        return {
            "feature": feature,
            "has_access": has_access,
            "required_tier": required_tier.value,
            "current_tier": current_tier.value,
            "upgrade_required": not has_access,
            "feature_info": FEATURE_INFO.get(pro_feature, {}),
        }

    def get_all_features_status(self, user_id: str) -> List[Dict[str, Any]]:
        """Get access status for all Pro features."""
        return [
            self.check_feature_access(user_id, feature.value)
            for feature in ProFeature
        ]

    # ==================== Stripe Integration ====================

    def create_checkout_session(
        self,
        user_id: str,
        email: str,
        price_id: str,
        success_url: str,
        cancel_url: str
    ) -> Dict[str, Any]:
        """Create a Stripe checkout session for subscription."""
        if not self.is_available():
            raise ValueError("Stripe is not configured")

        # Get or create Stripe customer
        user = self.db.get_user(user_id)
        customer_id = user.get("stripe_customer_id") if user else None

        if not customer_id:
            # Create new Stripe customer
            customer = stripe.Customer.create(
                email=email,
                metadata={"user_id": user_id}
            )
            customer_id = customer.id

            # Save customer ID
            self.db.update_user_subscription(
                user_id=user_id,
                subscription_tier="free",
                stripe_customer_id=customer_id
            )

        # Create checkout session
        session = stripe.checkout.Session.create(
            customer=customer_id,
            mode="subscription",
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={"user_id": user_id},
            subscription_data={"metadata": {"user_id": user_id}},
        )

        return {
            "checkout_url": session.url,
            "session_id": session.id,
        }

    def create_portal_session(self, user_id: str, return_url: str) -> Dict[str, Any]:
        """Create a Stripe customer portal session for subscription management."""
        if not self.is_available():
            raise ValueError("Stripe is not configured")

        user = self.db.get_user(user_id)
        if not user or not user.get("stripe_customer_id"):
            raise ValueError("User does not have a Stripe customer account")

        session = stripe.billing_portal.Session.create(
            customer=user["stripe_customer_id"],
            return_url=return_url,
        )

        return {
            "portal_url": session.url,
        }

    # ==================== Webhook Handlers ====================

    def handle_webhook(self, payload: bytes, signature: str) -> Dict[str, Any]:
        """Handle incoming Stripe webhook events."""
        if not self.is_available():
            raise ValueError("Stripe is not configured")

        # Never process webhooks without signature verification
        if not STRIPE_WEBHOOK_SECRET:
            raise ValueError("Webhook secret not configured - rejecting event")

        # Verify webhook signature
        try:
            event = stripe.Webhook.construct_event(
                payload, signature, STRIPE_WEBHOOK_SECRET
            )
        except stripe.error.SignatureVerificationError:
            raise ValueError("Invalid webhook signature")
        except ValueError:
            raise ValueError("Invalid webhook payload")

        # Handle different event types
        event_type = event["type"]
        data = event["data"]["object"]

        handlers = {
            "checkout.session.completed": self._handle_checkout_completed,
            "customer.subscription.updated": self._handle_subscription_updated,
            "customer.subscription.deleted": self._handle_subscription_deleted,
            "invoice.payment_failed": self._handle_payment_failed,
        }

        handler = handlers.get(event_type)
        if handler:
            return handler(data)

        return {"status": "ignored", "event_type": event_type}

    def _handle_checkout_completed(self, session: Dict[str, Any]) -> Dict[str, Any]:
        """Handle successful checkout - upgrade user to Pro."""
        user_id = session.get("metadata", {}).get("user_id")
        if not user_id:
            return {"status": "error", "message": "No user_id in metadata"}

        subscription_id = session.get("subscription")

        # Update user to Pro tier
        self.db.update_user_subscription(
            user_id=user_id,
            subscription_tier="pro",
            stripe_subscription_id=subscription_id,
            subscription_status="active"
        )

        return {"status": "success", "user_id": user_id, "tier": "pro"}

    def _handle_subscription_updated(self, subscription: Dict[str, Any]) -> Dict[str, Any]:
        """Handle subscription updates (status changes, plan changes)."""
        customer_id = subscription.get("customer")
        user = self.db.get_user_by_stripe_customer(customer_id)

        if not user:
            return {"status": "error", "message": "User not found for customer"}

        status = subscription.get("status")

        # Map Stripe status to our status
        status_map = {
            "active": "active",
            "past_due": "past_due",
            "canceled": "canceled",
            "incomplete": "incomplete",
            "trialing": "trialing",
        }

        self.db.update_user_subscription(
            user_id=user["user_id"],
            subscription_tier="pro" if status == "active" else user.get("subscription_tier", "free"),
            subscription_status=status_map.get(status, status)
        )

        return {"status": "success", "user_id": user["user_id"], "subscription_status": status}

    def _handle_subscription_deleted(self, subscription: Dict[str, Any]) -> Dict[str, Any]:
        """Handle subscription cancellation - downgrade to Free."""
        customer_id = subscription.get("customer")
        user = self.db.get_user_by_stripe_customer(customer_id)

        if not user:
            return {"status": "error", "message": "User not found for customer"}

        # Downgrade to free tier
        self.db.update_user_subscription(
            user_id=user["user_id"],
            subscription_tier="free",
            subscription_status="canceled"
        )

        return {"status": "success", "user_id": user["user_id"], "tier": "free"}

    def _handle_payment_failed(self, invoice: Dict[str, Any]) -> Dict[str, Any]:
        """Handle failed payment - mark subscription as past_due."""
        customer_id = invoice.get("customer")
        user = self.db.get_user_by_stripe_customer(customer_id)

        if not user:
            return {"status": "error", "message": "User not found for customer"}

        self.db.update_user_subscription(
            user_id=user["user_id"],
            subscription_tier=user.get("subscription_tier", "free"),
            subscription_status="past_due"
        )

        return {"status": "success", "user_id": user["user_id"], "subscription_status": "past_due"}


# Singleton instance
_subscription_service: Optional[SubscriptionService] = None


def get_subscription_service() -> SubscriptionService:
    """Get the subscription service singleton."""
    global _subscription_service
    if _subscription_service is None:
        _subscription_service = SubscriptionService()
    return _subscription_service
