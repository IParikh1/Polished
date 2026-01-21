"""
Redis Cache Service for Polished Resume Ranking System.
Provides caching for batch operations and rate limiting.
"""

import json
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import os
import hashlib

# Try to import Redis
try:
    import redis
    from redis import Redis
    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False
    Redis = None

# Configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CACHE_PREFIX = "polished:"
DEFAULT_TTL = 3600  # 1 hour
BATCH_TTL = 7200  # 2 hours
RANKING_TTL = 1800  # 30 minutes


class InMemoryCache:
    """Fallback in-memory cache when Redis is not available."""

    def __init__(self):
        self._cache: Dict[str, tuple] = {}  # key -> (value, expiry_time)

    def _cleanup(self):
        """Remove expired entries."""
        now = datetime.utcnow()
        expired = [k for k, (_, exp) in self._cache.items() if exp and exp < now]
        for k in expired:
            del self._cache[k]

    def get(self, key: str) -> Optional[str]:
        self._cleanup()
        if key in self._cache:
            value, expiry = self._cache[key]
            if expiry is None or expiry > datetime.utcnow():
                return value
            del self._cache[key]
        return None

    def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        expiry = datetime.utcnow() + timedelta(seconds=ex) if ex else None
        self._cache[key] = (value, expiry)
        return True

    def delete(self, key: str) -> int:
        if key in self._cache:
            del self._cache[key]
            return 1
        return 0

    def exists(self, key: str) -> int:
        self._cleanup()
        return 1 if key in self._cache else 0

    def keys(self, pattern: str) -> List[str]:
        self._cleanup()
        # Simple pattern matching (only supports prefix*)
        if pattern.endswith("*"):
            prefix = pattern[:-1]
            return [k for k in self._cache.keys() if k.startswith(prefix)]
        return [k for k in self._cache.keys() if k == pattern]

    def incr(self, key: str) -> int:
        value = self.get(key)
        new_value = int(value or 0) + 1
        self.set(key, str(new_value))
        return new_value

    def expire(self, key: str, seconds: int) -> bool:
        if key in self._cache:
            value, _ = self._cache[key]
            expiry = datetime.utcnow() + timedelta(seconds=seconds)
            self._cache[key] = (value, expiry)
            return True
        return False

    def ttl(self, key: str) -> int:
        if key in self._cache:
            _, expiry = self._cache[key]
            if expiry:
                remaining = (expiry - datetime.utcnow()).total_seconds()
                return max(0, int(remaining))
            return -1  # No expiry
        return -2  # Key doesn't exist

    def flushdb(self):
        self._cache.clear()


class BatchCache:
    """Cache service for batch operations."""

    def __init__(self):
        if HAS_REDIS:
            try:
                self.redis: Union[Redis, InMemoryCache] = redis.from_url(
                    REDIS_URL,
                    decode_responses=True,
                    socket_connect_timeout=5
                )
                # Test connection
                self.redis.ping()
                self._using_redis = True
            except Exception as e:
                print(f"Redis connection failed, using in-memory cache: {e}")
                self.redis = InMemoryCache()
                self._using_redis = False
        else:
            print("Redis not installed, using in-memory cache")
            self.redis = InMemoryCache()
            self._using_redis = False

    def _key(self, *parts: str) -> str:
        """Generate cache key with prefix."""
        return CACHE_PREFIX + ":".join(parts)

    # ==================== Batch Caching ====================

    def cache_batch(self, batch_id: str, batch_data: Dict[str, Any]) -> bool:
        """Cache batch metadata."""
        key = self._key("batch", batch_id)
        try:
            self.redis.set(key, json.dumps(batch_data, default=str), ex=BATCH_TTL)
            return True
        except Exception as e:
            print(f"Error caching batch: {e}")
            return False

    def get_cached_batch(self, batch_id: str) -> Optional[Dict[str, Any]]:
        """Get cached batch metadata."""
        key = self._key("batch", batch_id)
        try:
            data = self.redis.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            print(f"Error getting cached batch: {e}")
            return None

    def invalidate_batch(self, batch_id: str) -> bool:
        """Invalidate batch cache."""
        key = self._key("batch", batch_id)
        try:
            self.redis.delete(key)
            # Also invalidate rankings
            self.invalidate_rankings(batch_id)
            return True
        except Exception as e:
            print(f"Error invalidating batch cache: {e}")
            return False

    # ==================== Ranking Caching ====================

    def cache_rankings(
        self,
        batch_id: str,
        rankings: List[Dict[str, Any]],
        filter_hash: Optional[str] = None
    ) -> bool:
        """Cache batch rankings."""
        suffix = f":{filter_hash}" if filter_hash else ""
        key = self._key("rankings", batch_id + suffix)
        try:
            self.redis.set(key, json.dumps(rankings, default=str), ex=RANKING_TTL)
            return True
        except Exception as e:
            print(f"Error caching rankings: {e}")
            return False

    def get_cached_rankings(
        self,
        batch_id: str,
        filter_hash: Optional[str] = None
    ) -> Optional[List[Dict[str, Any]]]:
        """Get cached rankings."""
        suffix = f":{filter_hash}" if filter_hash else ""
        key = self._key("rankings", batch_id + suffix)
        try:
            data = self.redis.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            print(f"Error getting cached rankings: {e}")
            return None

    def invalidate_rankings(self, batch_id: str) -> bool:
        """Invalidate all rankings for a batch."""
        pattern = self._key("rankings", batch_id + "*")
        try:
            keys = self.redis.keys(pattern)
            for key in keys:
                self.redis.delete(key)
            return True
        except Exception as e:
            print(f"Error invalidating rankings: {e}")
            return False

    # ==================== Resume Caching ====================

    def cache_resume(
        self,
        batch_id: str,
        resume_id: str,
        resume_data: Dict[str, Any]
    ) -> bool:
        """Cache resume data."""
        key = self._key("resume", batch_id, resume_id)
        try:
            self.redis.set(key, json.dumps(resume_data, default=str), ex=DEFAULT_TTL)
            return True
        except Exception as e:
            print(f"Error caching resume: {e}")
            return False

    def get_cached_resume(
        self,
        batch_id: str,
        resume_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get cached resume data."""
        key = self._key("resume", batch_id, resume_id)
        try:
            data = self.redis.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            print(f"Error getting cached resume: {e}")
            return None

    def invalidate_resume(self, batch_id: str, resume_id: str) -> bool:
        """Invalidate resume cache."""
        key = self._key("resume", batch_id, resume_id)
        try:
            self.redis.delete(key)
            return True
        except Exception as e:
            print(f"Error invalidating resume cache: {e}")
            return False

    # ==================== Processing Status ====================

    def set_processing_status(
        self,
        batch_id: str,
        status: str,
        progress: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Set batch processing status."""
        key = self._key("processing", batch_id)
        data = {
            "status": status,
            "updated_at": datetime.utcnow().isoformat(),
            "progress": progress or {}
        }
        try:
            self.redis.set(key, json.dumps(data), ex=3600)  # 1 hour TTL
            return True
        except Exception as e:
            print(f"Error setting processing status: {e}")
            return False

    def get_processing_status(self, batch_id: str) -> Optional[Dict[str, Any]]:
        """Get batch processing status."""
        key = self._key("processing", batch_id)
        try:
            data = self.redis.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            print(f"Error getting processing status: {e}")
            return None

    def clear_processing_status(self, batch_id: str) -> bool:
        """Clear processing status."""
        key = self._key("processing", batch_id)
        try:
            self.redis.delete(key)
            return True
        except Exception as e:
            print(f"Error clearing processing status: {e}")
            return False

    # ==================== Rate Limiting ====================

    def check_rate_limit(
        self,
        identifier: str,
        limit: int = 100,
        window: int = 60
    ) -> tuple[bool, int]:
        """
        Check rate limit for an identifier.

        Args:
            identifier: User or IP identifier
            limit: Maximum requests per window
            window: Time window in seconds

        Returns:
            Tuple of (allowed, remaining)
        """
        key = self._key("ratelimit", identifier)
        try:
            current = self.redis.incr(key)

            # Set expiry on first request
            if current == 1:
                self.redis.expire(key, window)

            remaining = max(0, limit - current)
            allowed = current <= limit

            return allowed, remaining

        except Exception as e:
            print(f"Error checking rate limit: {e}")
            return True, limit  # Allow on error

    def get_rate_limit_status(
        self,
        identifier: str,
        limit: int = 100
    ) -> Dict[str, Any]:
        """Get current rate limit status."""
        key = self._key("ratelimit", identifier)
        try:
            current = int(self.redis.get(key) or 0)
            ttl = self.redis.ttl(key)

            return {
                "current": current,
                "limit": limit,
                "remaining": max(0, limit - current),
                "reset_in": max(0, ttl)
            }
        except Exception as e:
            print(f"Error getting rate limit status: {e}")
            return {"current": 0, "limit": limit, "remaining": limit, "reset_in": 0}

    # ==================== Utility Methods ====================

    def generate_filter_hash(self, filters: Dict[str, Any]) -> str:
        """Generate hash for filter parameters."""
        filter_str = json.dumps(filters, sort_keys=True, default=str)
        return hashlib.md5(filter_str.encode()).hexdigest()[:12]

    def flush_all(self) -> bool:
        """Flush all cache (use with caution)."""
        try:
            self.redis.flushdb()
            return True
        except Exception as e:
            print(f"Error flushing cache: {e}")
            return False

    def health_check(self) -> Dict[str, Any]:
        """Check cache health."""
        try:
            if self._using_redis:
                self.redis.ping()

            return {
                "status": "healthy",
                "backend": "redis" if self._using_redis else "memory",
                "connected": True
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "backend": "redis" if self._using_redis else "memory",
                "connected": False,
                "error": str(e)
            }


# Singleton instance
_batch_cache: Optional[BatchCache] = None


def get_cache() -> BatchCache:
    """Get the batch cache singleton."""
    global _batch_cache
    if _batch_cache is None:
        _batch_cache = BatchCache()
    return _batch_cache
