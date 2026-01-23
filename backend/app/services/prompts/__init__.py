"""
Tech Sales Resume Optimization Prompts for Polished.

This module contains specialized prompts for tech sales resume optimization,
including role-specific prompts, JD matching, and metrics extraction.
"""

from .base_sales_prompt import BASE_TECH_SALES_PROMPT
from .jd_matching import JD_MATCHING_PROMPT
from .metrics_extraction import METRICS_EXTRACTION_PROMPT
from .rewrite import REWRITE_PROMPT
from .role_prompts import get_role_prompt, ROLE_PROMPTS

__all__ = [
    "BASE_TECH_SALES_PROMPT",
    "JD_MATCHING_PROMPT",
    "METRICS_EXTRACTION_PROMPT",
    "REWRITE_PROMPT",
    "get_role_prompt",
    "ROLE_PROMPTS",
]
