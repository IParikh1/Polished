"""
Rate limiting for API usage based on user plan.
Free users: 3 reviews per month
Pro users: Unlimited
"""

import logging
import os
from datetime import datetime, timedelta
from typing import Tuple, Dict, Any, Optional
from enum import Enum

# Gracefully handle missing redis dependency
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None
    logging.getLogger(__name__).warning("redis not installed. Rate limiting will be permissive.")

logger = logging.getLogger(__name__)


class PlanType(str, Enum):
    ANONYMOUS = "anonymous"
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class UsageLimits:
    """Plan-based usage limits."""

    LIMITS = {
        PlanType.ANONYMOUS: 1,      # 1 review per session (must sign up for more)
        PlanType.FREE: 3,           # 3 reviews per month
        PlanType.PRO: 999999,       # Unlimited
        PlanType.ENTERPRISE: 999999  # Unlimited
    }

    @classmethod
    def get_limit(cls, plan: PlanType) -> int:
        return cls.LIMITS.get(plan, 3)


class RateLimiter:
    """Enforce usage limits per plan."""

    def __init__(self):
        if not REDIS_AVAILABLE:
            logger.warning("Redis not available for rate limiting. Using permissive mode.")
            self.redis = None
            return

        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        try:
            self.redis = redis.from_url(redis_url, decode_responses=True)
            self.redis.ping()
        except redis.ConnectionError:
            logger.warning("Redis connection failed. Using permissive mode.")
            self.redis = None

    def _usage_key(self, user_id: str) -> str:
        """Generate Redis key for usage tracking."""
        # Monthly reset - key includes year-month
        month_key = datetime.utcnow().strftime("%Y-%m")
        return f"usage:{user_id}:{month_key}"

    def check_limit(self, user_id: str, plan: PlanType = PlanType.FREE) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if user can make a request.
        Returns (allowed, usage_info)
        """
        limit = UsageLimits.get_limit(plan)

        if not self.redis:
            # Permissive mode when Redis is unavailable
            return True, {
                "plan": plan.value,
                "used": 0,
                "limit": limit,
                "remaining": limit,
                "message": "Rate limiting unavailable"
            }

        current_usage = int(self.redis.get(self._usage_key(user_id)) or 0)
        remaining = limit - current_usage
        allowed = remaining > 0

        # Calculate reset time (first of next month)
        now = datetime.utcnow()
        if now.month == 12:
            reset_date = datetime(now.year + 1, 1, 1)
        else:
            reset_date = datetime(now.year, now.month + 1, 1)

        usage_info = {
            "plan": plan.value,
            "used": current_usage,
            "limit": limit,
            "remaining": max(0, remaining),
            "resets_at": reset_date.isoformat()
        }

        if not allowed:
            usage_info["message"] = f"You've used all {limit} free reviews this month. Upgrade to Pro for unlimited reviews."

        return allowed, usage_info

    def increment_usage(self, user_id: str, plan: PlanType = PlanType.FREE) -> Dict[str, Any]:
        """
        Increment usage counter after successful request.
        Returns updated usage info.
        """
        if not self.redis:
            return {"message": "Rate limiting unavailable"}

        key = self._usage_key(user_id)

        # Increment and set expiry to end of month + buffer
        pipe = self.redis.pipeline()
        pipe.incr(key)
        pipe.expire(key, 35 * 24 * 60 * 60)  # 35 days
        results = pipe.execute()

        new_count = results[0]
        limit = UsageLimits.get_limit(plan)

        return {
            "plan": plan.value,
            "used": new_count,
            "limit": limit,
            "remaining": max(0, limit - new_count)
        }

    def get_usage(self, user_id: str, plan: PlanType = PlanType.FREE) -> Dict[str, Any]:
        """Get current usage without incrementing."""
        allowed, usage_info = self.check_limit(user_id, plan)
        return usage_info

    def check_and_increment(self, user_id: str, plan: PlanType = PlanType.FREE) -> Tuple[bool, Dict[str, Any]]:
        """
        Check limit and increment if allowed.
        Atomic operation to prevent race conditions.
        Returns (allowed, usage_info)
        """
        allowed, usage_info = self.check_limit(user_id, plan)

        if allowed and self.redis:
            usage_info = self.increment_usage(user_id, plan)
            if "remaining" in usage_info:
                usage_info["remaining"] = max(0, usage_info["remaining"])

        return allowed, usage_info

    def reset_usage(self, user_id: str) -> bool:
        """Reset usage for a user (admin function)."""
        if self.redis:
            self.redis.delete(self._usage_key(user_id))
        return True


# Singleton instance
rate_limiter = RateLimiter()
