"""
Response caching for common resume improvement suggestions.
Reduces Claude API calls by ~15-25% by caching generic advice.
"""

import hashlib
import logging
import os
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

import redis

logger = logging.getLogger(__name__)


class ResponseCache:
    """Cache common responses to reduce Claude API costs."""

    # Cache TTL settings
    GENERIC_ADVICE_TTL = 3600 * 24  # 24 hours for generic advice
    ROLE_SPECIFIC_TTL = 3600 * 6    # 6 hours for role-specific advice

    # Common questions that have largely similar answers
    CACHEABLE_PATTERNS = [
        "how to write a summary",
        "what action verbs",
        "ats optimization",
        "how long should",
        "one page or two",
        "should i include",
        "cover letter",
        "linkedin",
        "skills section",
        "education section",
        "gap in employment",
        "career change",
        "entry level",
        "no experience",
    ]

    def __init__(self):
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        try:
            self.redis = redis.from_url(redis_url, decode_responses=True)
            self.redis.ping()
            logger.info("Response cache connected to Redis")
        except redis.ConnectionError:
            logger.warning("Redis not available for response caching")
            self.redis = None
            self._fallback_cache: Dict[str, Dict[str, Any]] = {}

    def _cache_key(self, query: str, context_type: str = "generic") -> str:
        """Generate cache key from query."""
        normalized = query.lower().strip()
        query_hash = hashlib.md5(normalized.encode()).hexdigest()[:12]
        return f"response_cache:{context_type}:{query_hash}"

    def _is_cacheable(self, query: str) -> bool:
        """Check if a query is likely to have a cacheable response."""
        query_lower = query.lower()
        return any(pattern in query_lower for pattern in self.CACHEABLE_PATTERNS)

    def get_cached_response(self, query: str, context_type: str = "generic") -> Optional[str]:
        """Get cached response if available."""
        if not self._is_cacheable(query):
            return None

        key = self._cache_key(query, context_type)

        if self.redis:
            cached = self.redis.get(key)
            if cached:
                logger.debug(f"Cache hit for query: {query[:50]}...")
                return cached
        else:
            entry = self._fallback_cache.get(key)
            if entry and entry.get("expires_at", datetime.min) > datetime.utcnow():
                return entry.get("response")

        return None

    def cache_response(
        self,
        query: str,
        response: str,
        context_type: str = "generic",
        ttl: Optional[int] = None
    ) -> bool:
        """Cache a response for future use."""
        if not self._is_cacheable(query):
            return False

        key = self._cache_key(query, context_type)
        ttl = ttl or (self.ROLE_SPECIFIC_TTL if context_type != "generic" else self.GENERIC_ADVICE_TTL)

        if self.redis:
            self.redis.setex(key, ttl, response)
            logger.debug(f"Cached response for: {query[:50]}...")
            return True
        else:
            self._fallback_cache[key] = {
                "response": response,
                "expires_at": datetime.utcnow() + timedelta(seconds=ttl)
            }
            return True

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        if self.redis:
            keys = self.redis.keys("response_cache:*")
            return {
                "cached_responses": len(keys),
                "cache_type": "redis"
            }
        else:
            valid_entries = sum(
                1 for entry in self._fallback_cache.values()
                if entry.get("expires_at", datetime.min) > datetime.utcnow()
            )
            return {
                "cached_responses": valid_entries,
                "cache_type": "memory"
            }

    def clear_cache(self) -> int:
        """Clear all cached responses."""
        if self.redis:
            keys = self.redis.keys("response_cache:*")
            if keys:
                return self.redis.delete(*keys)
            return 0
        else:
            count = len(self._fallback_cache)
            self._fallback_cache.clear()
            return count


# Pre-defined generic advice that doesn't need API calls
GENERIC_ADVICE = {
    "action_verbs": """Strong action verbs for resumes:

**Leadership:** Led, Directed, Managed, Oversaw, Coordinated, Orchestrated
**Achievement:** Achieved, Exceeded, Delivered, Accomplished, Attained
**Creation:** Developed, Built, Designed, Created, Architected, Engineered
**Improvement:** Optimized, Streamlined, Enhanced, Improved, Accelerated
**Analysis:** Analyzed, Evaluated, Assessed, Identified, Investigated
**Communication:** Presented, Negotiated, Collaborated, Facilitated

Avoid weak verbs like: Helped, Worked on, Was responsible for, Assisted with""",

    "ats_tips": """ATS Optimization Tips:

1. **Use standard section headings:** "Experience", "Education", "Skills" (not creative alternatives)
2. **Include keywords from the job posting** - match exact phrases
3. **Avoid tables, graphics, headers/footers** - ATS can't parse them
4. **Use standard fonts** - Arial, Calibri, Times New Roman
5. **Save as .docx or .pdf** (check job posting preference)
6. **Spell out acronyms once:** "Search Engine Optimization (SEO)"
7. **Use standard date formats:** "Jan 2020 - Present" or "01/2020 - Present"
8. **List skills in a dedicated section** with relevant keywords""",

    "resume_length": """Resume Length Guidelines:

**One page:** Entry-level to ~7 years experience
**Two pages:** 8+ years, senior roles, or highly technical positions
**Never exceed two pages** unless academic CV or federal resume

Tips for fitting on one page:
- Remove outdated experience (>10-15 years old)
- Condense early career roles to 1-2 bullets
- Use concise language (remove "responsible for", "helped with")
- Adjust margins to 0.5-0.75 inches
- Use 10-11pt font (never below 10pt)"""
}


def get_generic_advice(topic: str) -> Optional[str]:
    """Get pre-defined generic advice without API call."""
    topic_lower = topic.lower()

    if any(word in topic_lower for word in ["action verb", "strong verb", "power verb"]):
        return GENERIC_ADVICE["action_verbs"]
    elif any(word in topic_lower for word in ["ats", "applicant tracking", "keyword"]):
        return GENERIC_ADVICE["ats_tips"]
    elif any(word in topic_lower for word in ["length", "one page", "two page", "how long"]):
        return GENERIC_ADVICE["resume_length"]

    return None


# Singleton instance
response_cache = ResponseCache()
