"""
Services module for Polished Resume Ranking System.
"""

from .aws_store import AWSStore, get_store
from .batch_processor import BatchProcessor, get_processor, ResumeParser, ResumeExtractor
from .batch_cache import BatchCache, get_cache
from .quick_scorer import QuickScorer, get_scorer, score_resume, ScoringWeights
from .premium_gate import (
    PremiumGate,
    get_premium_gate,
    PremiumTier,
    PremiumFeature,
    require_feature,
)

__all__ = [
    # AWS Store
    "AWSStore",
    "get_store",
    # Batch Processor
    "BatchProcessor",
    "get_processor",
    "ResumeParser",
    "ResumeExtractor",
    # Cache
    "BatchCache",
    "get_cache",
    # Quick Scorer
    "QuickScorer",
    "get_scorer",
    "score_resume",
    "ScoringWeights",
    # Premium Gate
    "PremiumGate",
    "get_premium_gate",
    "PremiumTier",
    "PremiumFeature",
    "require_feature",
]
