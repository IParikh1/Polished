"""
Role-specific prompts for tech sales resume optimization.
"""

from typing import Optional
from .entry_sdr import ENTRY_SDR_PROMPT
from .sdr import SDR_PROMPT
from .ae import AE_PROMPT
from .senior_ae import SENIOR_AE_PROMPT
from .am import AM_PROMPT
from .sales_manager import SALES_MANAGER_PROMPT

# Map role identifiers to their prompts
ROLE_PROMPTS = {
    "entry_sdr": ENTRY_SDR_PROMPT,
    "sdr": SDR_PROMPT,
    "account_executive": AE_PROMPT,
    "senior_ae": SENIOR_AE_PROMPT,
    "account_manager": AM_PROMPT,
    "sales_manager": SALES_MANAGER_PROMPT,
}

# Human-readable role names
ROLE_DISPLAY_NAMES = {
    "entry_sdr": "Entry-Level SDR (0-1 years)",
    "sdr": "SDR/BDR (1-3 years)",
    "account_executive": "Account Executive (2-5 years)",
    "senior_ae": "Senior/Enterprise AE (5+ years)",
    "account_manager": "Account Manager / CSM",
    "sales_manager": "Sales Manager / Director",
}


def get_role_prompt(role: str) -> Optional[str]:
    """
    Get the role-specific prompt for a given role.

    Args:
        role: Role identifier (e.g., 'entry_sdr', 'ae', 'senior_ae')

    Returns:
        Role-specific prompt string, or None if role not found
    """
    return ROLE_PROMPTS.get(role)


def get_role_display_name(role: str) -> str:
    """
    Get the human-readable display name for a role.

    Args:
        role: Role identifier

    Returns:
        Human-readable role name
    """
    return ROLE_DISPLAY_NAMES.get(role, role.replace("_", " ").title())


__all__ = [
    "ENTRY_SDR_PROMPT",
    "SDR_PROMPT",
    "AE_PROMPT",
    "SENIOR_AE_PROMPT",
    "AM_PROMPT",
    "SALES_MANAGER_PROMPT",
    "ROLE_PROMPTS",
    "ROLE_DISPLAY_NAMES",
    "get_role_prompt",
    "get_role_display_name",
]
