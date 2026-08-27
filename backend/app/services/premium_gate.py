"""
Premium Feature Gate Service for Polished Resume Ranking System.
Controls access to premium features and handles feature flags.
"""

from typing import Dict, List, Optional, Any, Set
from datetime import datetime, timedelta
from enum import Enum
import os


class PremiumTier(str, Enum):
    """Premium subscription tiers."""
    FREE = "free"
    BASIC = "basic"  # JD Matching
    PRO = "pro"  # JD Matching + Deep Analysis
    ENTERPRISE = "enterprise"  # All features


class PremiumFeature(str, Enum):
    """Available premium features."""
    JD_MATCHING = "jd_matching"
    DEEP_ANALYSIS = "deep_analysis"
    CONSULTING = "consulting"
    RESUME_WRITING = "resume_writing"
    BULK_EXPORT = "bulk_export"
    API_ACCESS = "api_access"
    PRIORITY_PROCESSING = "priority_processing"
    CUSTOM_SCORING = "custom_scoring"
    PLACEMENT_TRACKING = "placement_tracking"


# Feature availability by tier
TIER_FEATURES: Dict[PremiumTier, Set[PremiumFeature]] = {
    PremiumTier.FREE: set(),
    PremiumTier.BASIC: {
        PremiumFeature.JD_MATCHING,
        PremiumFeature.BULK_EXPORT,
    },
    PremiumTier.PRO: {
        PremiumFeature.JD_MATCHING,
        PremiumFeature.DEEP_ANALYSIS,
        PremiumFeature.RESUME_WRITING,
        PremiumFeature.BULK_EXPORT,
        PremiumFeature.API_ACCESS,
        PremiumFeature.PRIORITY_PROCESSING,
    },
    PremiumTier.ENTERPRISE: {
        PremiumFeature.JD_MATCHING,
        PremiumFeature.DEEP_ANALYSIS,
        PremiumFeature.CONSULTING,
        PremiumFeature.RESUME_WRITING,
        PremiumFeature.BULK_EXPORT,
        PremiumFeature.API_ACCESS,
        PremiumFeature.PRIORITY_PROCESSING,
        PremiumFeature.CUSTOM_SCORING,
        PremiumFeature.PLACEMENT_TRACKING,
    },
}

# Usage limits by tier
TIER_LIMITS: Dict[PremiumTier, Dict[str, int]] = {
    PremiumTier.FREE: {
        "batches_per_month": 5,
        "resumes_per_batch": 50,
        "total_resumes_per_month": 100,
        "exports_per_month": 10,
        "api_calls_per_day": 0,
    },
    PremiumTier.BASIC: {
        "batches_per_month": 20,
        "resumes_per_batch": 200,
        "total_resumes_per_month": 1000,
        "exports_per_month": 50,
        "api_calls_per_day": 100,
    },
    PremiumTier.PRO: {
        "batches_per_month": 100,
        "resumes_per_batch": 500,
        "total_resumes_per_month": 10000,
        "exports_per_month": 500,
        "api_calls_per_day": 1000,
    },
    PremiumTier.ENTERPRISE: {
        "batches_per_month": -1,  # Unlimited
        "resumes_per_batch": -1,
        "total_resumes_per_month": -1,
        "exports_per_month": -1,
        "api_calls_per_day": -1,
    },
}

# Feature pricing (for pay-per-use)
FEATURE_PRICING: Dict[PremiumFeature, Dict[str, float]] = {
    PremiumFeature.JD_MATCHING: {
        "per_resume": 0.10,
        "per_batch": 5.00,
    },
    PremiumFeature.DEEP_ANALYSIS: {
        "per_resume": 0.50,
        "per_batch": 25.00,
    },
    PremiumFeature.CONSULTING: {
        "per_session": 10.00,
        "per_rewrite": 5.00,
    },
    PremiumFeature.RESUME_WRITING: {
        "per_resume": 2.00,
        "per_export": 1.00,
        "per_section_rewrite": 0.50,
    },
}

# Tier pricing
TIER_PRICING: Dict[PremiumTier, Dict[str, float]] = {
    PremiumTier.FREE: {"monthly": 0, "yearly": 0},
    PremiumTier.BASIC: {"monthly": 29, "yearly": 290},
    PremiumTier.PRO: {"monthly": 99, "yearly": 990},
    PremiumTier.ENTERPRISE: {"monthly": 499, "yearly": 4990},
}


class PremiumGate:
    """
    Service for managing premium feature access.
    In MVP mode, this can be simplified or bypassed.
    """

    def __init__(self, bypass_mode: bool = False):
        """
        Initialize premium gate.

        Args:
            bypass_mode: If True, all features are available (for MVP/testing)
        """
        # Bypass unlocks every paid feature - never honor it in production
        is_production = os.getenv("ENVIRONMENT", "development").lower() == "production"
        env_bypass = os.getenv("PREMIUM_BYPASS", "").lower() == "true"
        self.bypass_mode = (bypass_mode or env_bypass) and not is_production
        self._user_tiers: Dict[str, PremiumTier] = {}
        self._usage_tracking: Dict[str, Dict[str, int]] = {}

    def set_user_tier(self, user_id: str, tier: PremiumTier) -> None:
        """Set user's premium tier."""
        self._user_tiers[user_id] = tier

    def get_user_tier(self, user_id: str) -> PremiumTier:
        """Get user's premium tier from database."""
        if self.bypass_mode:
            return PremiumTier.ENTERPRISE

        # Check in-memory cache first
        if user_id in self._user_tiers:
            return self._user_tiers[user_id]

        # Query database for user tier
        try:
            from ..aws.dynamodb import get_db
            db = get_db()
            user = db.get_user(user_id)
            if user:
                # Admin users get enterprise tier
                if user.get("is_admin", False):
                    self._user_tiers[user_id] = PremiumTier.ENTERPRISE
                    return PremiumTier.ENTERPRISE

                tier_str = user.get("subscription_tier", "free")
                tier = PremiumTier(tier_str)
                self._user_tiers[user_id] = tier  # Cache it
                return tier
        except Exception as e:
            print(f"Error fetching user tier: {e}")

        return PremiumTier.FREE

    def is_admin(self, user_id: str) -> bool:
        """Check if user is an admin."""
        try:
            from ..aws.dynamodb import get_db
            db = get_db()
            return db.is_user_admin(user_id)
        except Exception:
            return False

    def has_feature(self, user_id: str, feature: PremiumFeature) -> bool:
        """Check if user has access to a feature."""
        if self.bypass_mode:
            return True

        tier = self.get_user_tier(user_id)
        return feature in TIER_FEATURES.get(tier, set())

    def check_features(
        self,
        user_id: str,
        features: List[PremiumFeature]
    ) -> Dict[str, bool]:
        """Check access to multiple features."""
        return {f.value: self.has_feature(user_id, f) for f in features}

    def get_available_features(self, user_id: str) -> List[PremiumFeature]:
        """Get list of features available to user."""
        if self.bypass_mode:
            return list(PremiumFeature)

        tier = self.get_user_tier(user_id)
        return list(TIER_FEATURES.get(tier, set()))

    def get_user_limits(self, user_id: str) -> Dict[str, int]:
        """Get usage limits for user."""
        if self.bypass_mode:
            return {k: -1 for k in TIER_LIMITS[PremiumTier.FREE].keys()}

        tier = self.get_user_tier(user_id)
        return TIER_LIMITS.get(tier, TIER_LIMITS[PremiumTier.FREE]).copy()

    def check_limit(
        self,
        user_id: str,
        limit_type: str,
        requested_amount: int = 1
    ) -> tuple[bool, int]:
        """
        Check if user is within usage limits.

        Returns:
            Tuple of (allowed, remaining)
        """
        if self.bypass_mode:
            return True, -1

        limits = self.get_user_limits(user_id)
        limit = limits.get(limit_type, 0)

        if limit == -1:  # Unlimited
            return True, -1

        # Get current usage
        user_usage = self._usage_tracking.get(user_id, {})
        current = user_usage.get(limit_type, 0)

        remaining = limit - current
        allowed = remaining >= requested_amount

        return allowed, remaining

    def increment_usage(
        self,
        user_id: str,
        limit_type: str,
        amount: int = 1
    ) -> bool:
        """Increment usage counter."""
        if user_id not in self._usage_tracking:
            self._usage_tracking[user_id] = {}

        current = self._usage_tracking[user_id].get(limit_type, 0)
        self._usage_tracking[user_id][limit_type] = current + amount
        return True

    def get_usage(self, user_id: str) -> Dict[str, int]:
        """Get current usage for user."""
        return self._usage_tracking.get(user_id, {}).copy()

    def reset_usage(self, user_id: str, limit_type: Optional[str] = None) -> bool:
        """Reset usage counters."""
        if user_id in self._usage_tracking:
            if limit_type:
                self._usage_tracking[user_id][limit_type] = 0
            else:
                self._usage_tracking[user_id] = {}
        return True

    def calculate_feature_cost(
        self,
        feature: PremiumFeature,
        quantity: int = 1,
        pricing_type: str = "per_resume"
    ) -> float:
        """Calculate cost for using a premium feature."""
        pricing = FEATURE_PRICING.get(feature, {})
        unit_price = pricing.get(pricing_type, 0)
        return unit_price * quantity

    def get_upgrade_options(self, user_id: str) -> List[Dict[str, Any]]:
        """Get available upgrade options for user."""
        current_tier = self.get_user_tier(user_id)
        tier_order = [PremiumTier.FREE, PremiumTier.BASIC, PremiumTier.PRO, PremiumTier.ENTERPRISE]

        current_index = tier_order.index(current_tier)
        upgrade_tiers = tier_order[current_index + 1:]

        options = []
        for tier in upgrade_tiers:
            options.append({
                "tier": tier.value,
                "features": [f.value for f in TIER_FEATURES[tier]],
                "limits": TIER_LIMITS[tier],
                "pricing": TIER_PRICING[tier],
            })

        return options

    def validate_batch_features(
        self,
        user_id: str,
        requested_features: List[str]
    ) -> Dict[str, Any]:
        """
        Validate that user can use requested premium features for a batch.

        Returns:
            Dict with 'valid', 'allowed_features', 'denied_features', 'cost'
        """
        result = {
            "valid": True,
            "allowed_features": [],
            "denied_features": [],
            "estimated_cost": 0,
        }

        for feature_str in requested_features:
            try:
                feature = PremiumFeature(feature_str)
                if self.has_feature(user_id, feature):
                    result["allowed_features"].append(feature_str)
                else:
                    result["denied_features"].append(feature_str)
                    result["valid"] = False
            except ValueError:
                result["denied_features"].append(feature_str)
                result["valid"] = False

        return result

    def get_feature_info(self, feature: PremiumFeature) -> Dict[str, Any]:
        """Get detailed information about a feature."""
        return {
            "feature": feature.value,
            "pricing": FEATURE_PRICING.get(feature, {}),
            "available_in_tiers": [
                tier.value for tier, features in TIER_FEATURES.items()
                if feature in features
            ],
            "description": self._get_feature_description(feature),
        }

    def _get_feature_description(self, feature: PremiumFeature) -> str:
        """Get feature description."""
        descriptions = {
            PremiumFeature.JD_MATCHING: "Match resumes against job descriptions with AI-powered skill matching",
            PremiumFeature.DEEP_ANALYSIS: "Get comprehensive LLM analysis of each resume with strengths, weaknesses, and recommendations",
            PremiumFeature.CONSULTING: "AI-powered resume consulting with rewrite suggestions and role optimization",
            PremiumFeature.BULK_EXPORT: "Export large batches to CSV/JSON with all scoring data",
            PremiumFeature.API_ACCESS: "Programmatic API access for integration with your systems",
            PremiumFeature.PRIORITY_PROCESSING: "Faster processing queue for your batches",
            PremiumFeature.CUSTOM_SCORING: "Configure custom scoring rules and weights",
            PremiumFeature.PLACEMENT_TRACKING: "Track successful placements and generate revenue reports",
        }
        return descriptions.get(feature, "Premium feature")


# Singleton instance
_premium_gate: Optional[PremiumGate] = None


def get_premium_gate(bypass_mode: bool = False) -> PremiumGate:
    """Get the premium gate singleton."""
    global _premium_gate
    if _premium_gate is None:
        # Check for MVP/development mode
        env_bypass = os.getenv("PREMIUM_BYPASS", "").lower() == "true"
        env_mode = os.getenv("ENVIRONMENT", "development").lower()
        bypass = bypass_mode or env_bypass or env_mode == "development"

        _premium_gate = PremiumGate(bypass_mode=bypass)
    return _premium_gate


def require_feature(feature: PremiumFeature):
    """
    Decorator to require a premium feature for an endpoint.

    Usage:
        @require_feature(PremiumFeature.DEEP_ANALYSIS)
        async def deep_analysis_endpoint(...):
            ...
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Get user_id from request (implementation depends on auth)
            user_id = kwargs.get("user_id", "anonymous")

            gate = get_premium_gate()
            if not gate.has_feature(user_id, feature):
                from fastapi import HTTPException
                raise HTTPException(
                    status_code=402,
                    detail={
                        "error": "Premium feature required",
                        "feature": feature.value,
                        "upgrade_options": gate.get_upgrade_options(user_id)
                    }
                )

            return await func(*args, **kwargs)
        return wrapper
    return decorator
