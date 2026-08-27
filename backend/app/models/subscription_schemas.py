"""
Subscription and user schemas for Polished Resume Ranking System.
Handles Stripe subscription data models.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum
from datetime import datetime


class SubscriptionTier(str, Enum):
    """Subscription tiers matching Stripe products."""
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class SubscriptionStatus(str, Enum):
    """Stripe subscription statuses."""
    ACTIVE = "active"
    CANCELED = "canceled"
    PAST_DUE = "past_due"
    INCOMPLETE = "incomplete"
    TRIALING = "trialing"


class ProFeature(str, Enum):
    """Features available in Pro tier."""
    JD_MATCHING = "jd_matching"
    DEEP_ANALYSIS = "deep_analysis"
    RESUME_WRITING = "resume_writing"
    CONSULTING = "consulting"
    BULK_EXPORT = "bulk_export"
    PRIORITY_PROCESSING = "priority_processing"


# Feature metadata for UI display
FEATURE_INFO = {
    ProFeature.JD_MATCHING: {
        "name": "JD Matching",
        "description": "Match resumes against job descriptions with AI-powered skill matching",
        "icon": "target",
    },
    ProFeature.DEEP_ANALYSIS: {
        "name": "Deep Analysis",
        "description": "Get comprehensive LLM analysis with strengths, weaknesses, and recommendations",
        "icon": "brain",
    },
    ProFeature.RESUME_WRITING: {
        "name": "Resume Writing",
        "description": "AI-powered resume generation optimized for your target role",
        "icon": "edit",
    },
    ProFeature.CONSULTING: {
        "name": "Resume Consulting",
        "description": "Interactive AI consulting per resume: analysis, section rewrites, and chat",
        "icon": "message-circle",
    },
    ProFeature.BULK_EXPORT: {
        "name": "Export to PDF/DOCX",
        "description": "Export resumes in professional formats with custom templates",
        "icon": "download",
    },
    ProFeature.PRIORITY_PROCESSING: {
        "name": "Priority Processing",
        "description": "Get faster processing for your resume batches",
        "icon": "zap",
    },
}


# ==================== Request/Response Models ====================

class UserProfile(BaseModel):
    """User profile from DynamoDB."""
    user_id: str
    email: str
    name: Optional[str] = None
    subscription_tier: SubscriptionTier = SubscriptionTier.FREE
    stripe_customer_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None
    subscription_status: Optional[SubscriptionStatus] = None
    is_admin: bool = False
    created_at: str
    updated_at: str


# ==================== Admin Models ====================

class UserUsage(BaseModel):
    """Usage metrics for a user."""
    user_id: str
    period: str  # Format: YYYY-MM
    batches_created: int = 0
    resumes_processed: int = 0
    exports_count: int = 0
    jd_matches: int = 0
    resume_writes: int = 0
    deep_analyses: int = 0
    updated_at: str


class UserCost(BaseModel):
    """Calculated cost for a user's usage."""
    batches_cost: float = 0.0
    resumes_cost: float = 0.0
    exports_cost: float = 0.0
    jd_matches_cost: float = 0.0
    resume_writes_cost: float = 0.0
    deep_analyses_cost: float = 0.0
    total_cost: float = 0.0


class AdminUserResponse(BaseModel):
    """User data for admin dashboard."""
    user_id: str
    email: str
    name: Optional[str] = None
    subscription_tier: SubscriptionTier
    subscription_status: Optional[SubscriptionStatus] = None
    is_admin: bool = False
    stripe_customer_id: Optional[str] = None
    created_at: str
    updated_at: str
    usage: Optional[UserUsage] = None
    cost: Optional[UserCost] = None


class AdminStatsResponse(BaseModel):
    """Aggregate statistics for admin dashboard."""
    total_users: int
    users_by_tier: dict  # {"free": 10, "pro": 5, "enterprise": 1}
    users_by_status: dict  # {"active": 10, "canceled": 2, ...}
    total_batches: int
    total_resumes: int
    total_revenue: float
    period: str  # Current month YYYY-MM


class AdminUserListResponse(BaseModel):
    """Response for admin user list."""
    users: List[AdminUserResponse]
    total: int
    limit: int
    offset: int


class SubscriptionResponse(BaseModel):
    """Subscription status response for frontend."""
    tier: SubscriptionTier
    status: Optional[SubscriptionStatus] = None
    is_pro: bool
    features: List[str]
    limits: dict
    upgrade_url: Optional[str] = None
    manage_url: Optional[str] = None


class CheckoutSessionRequest(BaseModel):
    """Request to create a Stripe checkout session."""
    price_id: str = Field(..., description="Stripe Price ID for the plan")
    success_url: str = Field(..., description="URL to redirect after successful payment")
    cancel_url: str = Field(..., description="URL to redirect if payment is canceled")


class CheckoutSessionResponse(BaseModel):
    """Checkout session response."""
    checkout_url: str
    session_id: str


class PortalSessionRequest(BaseModel):
    """Request to create a Stripe customer portal session."""
    return_url: str = Field(..., description="URL to return to after portal session")


class PortalSessionResponse(BaseModel):
    """Customer portal session response."""
    portal_url: str


class FeatureAccessResponse(BaseModel):
    """Response for checking feature access."""
    feature: str
    has_access: bool
    required_tier: SubscriptionTier
    current_tier: SubscriptionTier
    upgrade_required: bool


class TierLimits(BaseModel):
    """Usage limits for a subscription tier."""
    batches_per_month: int
    resumes_per_batch: int
    total_resumes_per_month: int
    exports_per_month: int


# Tier limits configuration
TIER_LIMITS = {
    SubscriptionTier.FREE: TierLimits(
        batches_per_month=5,
        resumes_per_batch=50,
        total_resumes_per_month=100,
        exports_per_month=10,
    ),
    SubscriptionTier.PRO: TierLimits(
        batches_per_month=100,
        resumes_per_batch=500,
        total_resumes_per_month=10000,
        exports_per_month=500,
    ),
    SubscriptionTier.ENTERPRISE: TierLimits(
        batches_per_month=-1,  # Unlimited
        resumes_per_batch=-1,
        total_resumes_per_month=-1,
        exports_per_month=-1,
    ),
}


# Features available per tier
TIER_FEATURES = {
    SubscriptionTier.FREE: set(),
    SubscriptionTier.PRO: {
        ProFeature.JD_MATCHING,
        ProFeature.DEEP_ANALYSIS,
        ProFeature.RESUME_WRITING,
        ProFeature.CONSULTING,
        ProFeature.BULK_EXPORT,
        ProFeature.PRIORITY_PROCESSING,
    },
    SubscriptionTier.ENTERPRISE: {
        ProFeature.JD_MATCHING,
        ProFeature.DEEP_ANALYSIS,
        ProFeature.RESUME_WRITING,
        ProFeature.CONSULTING,
        ProFeature.BULK_EXPORT,
        ProFeature.PRIORITY_PROCESSING,
    },
}
