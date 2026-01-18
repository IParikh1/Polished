"""
Redis-backed session storage with 24-hour TTL.
All resume data is automatically deleted after 24 hours.
"""

import json
import logging
import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from zoneinfo import ZoneInfo

# Use EST timezone for all timestamps
EST = ZoneInfo("America/New_York")


def now_est() -> datetime:
    """Get current datetime in EST timezone."""
    return datetime.now(EST)

# Gracefully handle missing redis dependency
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None
    logging.getLogger(__name__).warning("redis not installed. Using in-memory session store.")

logger = logging.getLogger(__name__)


class SessionStore:
    """Redis-backed session storage with automatic 24-hour expiry."""

    TTL_HOURS = 24
    TTL_SECONDS = TTL_HOURS * 60 * 60

    def __init__(self):
        self._fallback_store: Dict[str, Dict] = {}

        if not REDIS_AVAILABLE:
            logger.warning("Redis not available. Using in-memory fallback.")
            self.redis = None
            return

        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        try:
            self.redis = redis.from_url(redis_url, decode_responses=True)
            self.redis.ping()
            logger.info("Connected to Redis successfully")
        except redis.ConnectionError as e:
            logger.warning(f"Redis connection failed: {e}. Using in-memory fallback.")
            self.redis = None

    def _key(self, session_id: str) -> str:
        """Generate Redis key for session."""
        return f"session:{session_id}"

    def create_session(self, session_id: str, resume_text: str) -> Dict[str, Any]:
        """Create new session with resume. Auto-expires in 24 hours."""
        session_data = {
            "session_id": session_id,
            "resume_text": resume_text,
            "messages": [],
            "corrections": [],
            "token_count": 0,
            "created_at": now_est().isoformat(),
            "expires_at": (now_est() + timedelta(hours=self.TTL_HOURS)).isoformat()
        }

        if self.redis:
            self.redis.setex(
                self._key(session_id),
                self.TTL_SECONDS,
                json.dumps(session_data)
            )
        else:
            self._fallback_store[session_id] = session_data

        logger.info(f"Created session {session_id[:8]}... (expires in {self.TTL_HOURS}h)")
        return session_data

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve session. Returns None if expired or not found."""
        if self.redis:
            data = self.redis.get(self._key(session_id))
            if data:
                # Refresh TTL on access (sliding expiration)
                self.redis.expire(self._key(session_id), self.TTL_SECONDS)
                return json.loads(data)
            return None
        else:
            return self._fallback_store.get(session_id)

    def update_session(self, session_id: str, session_data: Dict[str, Any]) -> bool:
        """Update session data. Resets TTL."""
        if self.redis:
            self.redis.setex(
                self._key(session_id),
                self.TTL_SECONDS,
                json.dumps(session_data)
            )
        else:
            self._fallback_store[session_id] = session_data
        return True

    def add_message(self, session_id: str, role: str, content: str, tokens: int = 0) -> bool:
        """Add message to session history."""
        session = self.get_session(session_id)
        if not session:
            return False

        session["messages"].append({
            "role": role,
            "content": content,
            "tokens": tokens,
            "timestamp": now_est().isoformat()
        })
        session["token_count"] += tokens

        return self.update_session(session_id, session)

    def add_correction(self, session_id: str, correction: str) -> bool:
        """Track user correction to prevent AI from repeating mistakes."""
        session = self.get_session(session_id)
        if not session:
            return False

        session["corrections"].append(correction)
        logger.info(f"Added correction to session {session_id[:8]}...")

        return self.update_session(session_id, session)

    def delete_session(self, session_id: str) -> bool:
        """Explicitly delete session (user request or cleanup)."""
        if self.redis:
            self.redis.delete(self._key(session_id))
        else:
            self._fallback_store.pop(session_id, None)

        logger.info(f"Deleted session {session_id[:8]}...")
        return True

    def session_exists(self, session_id: str) -> bool:
        """Check if session exists."""
        if self.redis:
            return self.redis.exists(self._key(session_id)) > 0
        return session_id in self._fallback_store

    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session metadata without full content (for API responses)."""
        session = self.get_session(session_id)
        if not session:
            return None

        return {
            "session_id": session_id,
            "has_resume": bool(session.get("resume_text")),
            "message_count": len(session.get("messages", [])),
            "correction_count": len(session.get("corrections", [])),
            "token_count": session.get("token_count", 0),
            "created_at": session.get("created_at"),
            "expires_at": session.get("expires_at")
        }

    def get_ttl(self, session_id: str) -> Optional[int]:
        """Get remaining TTL in seconds."""
        if self.redis:
            ttl = self.redis.ttl(self._key(session_id))
            return ttl if ttl > 0 else None
        return None


# Singleton instance
session_store = SessionStore()
