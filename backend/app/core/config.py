"""
Application configuration.
Loads from environment variables with sensible defaults.
"""

import os
from dotenv import load_dotenv

load_dotenv()


# =============================================================================
# API Keys
# =============================================================================
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# =============================================================================
# Redis (Session Storage)
# =============================================================================
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
SESSION_TTL_HOURS = int(os.getenv("SESSION_TTL_HOURS", "24"))

# =============================================================================
# Database (Users/Billing only - NO resume storage)
# =============================================================================
DATABASE_URL = os.getenv("DATABASE_URL", "")

# =============================================================================
# Stripe (Billing)
# =============================================================================
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
STRIPE_PRICE_PRO = os.getenv("STRIPE_PRICE_PRO", "")  # price_xxx for $9/mo
STRIPE_PRICE_ENTERPRISE = os.getenv("STRIPE_PRICE_ENTERPRISE", "")

# =============================================================================
# App Settings
# =============================================================================
APP_NAME = "Polished"
APP_VERSION = "1.1.0"
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

# Frontend URL (for Stripe redirects)
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

# =============================================================================
# LLM Settings
# =============================================================================
LLM_MODEL = os.getenv("LLM_MODEL", "claude-sonnet-4-20250514")
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "4096"))

# =============================================================================
# Rate Limiting
# =============================================================================
FREE_TIER_LIMIT = int(os.getenv("FREE_TIER_LIMIT", "3"))  # Reviews per month
ANONYMOUS_LIMIT = int(os.getenv("ANONYMOUS_LIMIT", "1"))  # Reviews per session

# =============================================================================
# CORS
# =============================================================================
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

# =============================================================================
# Google Sheets (Legacy - for waitlist)
# =============================================================================
GOOGLE_SHEETS_CREDENTIALS = os.getenv("GOOGLE_SHEETS_CREDENTIALS", "")
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID", "")


def validate_config():
    """Validate required configuration on startup."""
    errors = []

    if not ANTHROPIC_API_KEY:
        errors.append("ANTHROPIC_API_KEY is required")

    if errors:
        raise ValueError(f"Configuration errors: {', '.join(errors)}")

    return True
