"""
Context window management for Claude API calls.
Optimizes token usage to control costs while maintaining conversation quality.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)


class ContextManager:
    """Manages Claude context window to control costs."""

    # Token limits - optimized for cost efficiency
    MAX_CONTEXT_TOKENS = 8000  # Leave room for response
    RESUME_TOKEN_ESTIMATE = 1500  # Average resume size
    SYSTEM_PROMPT_TOKENS = 800  # Optimized system prompt (down from 1500)
    MAX_MESSAGES_TO_KEEP = 8  # Reduced from 10 for cost savings

    # Cost tracking (Claude Sonnet pricing)
    INPUT_COST_PER_1K = 0.003  # $3/1M input tokens
    OUTPUT_COST_PER_1K = 0.015  # $15/1M output tokens

    def __init__(self):
        self._session_tokens: Dict[str, Dict[str, int]] = {}

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count (rough approximation: 4 chars = 1 token)."""
        return len(text) // 4

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost for a request in dollars."""
        input_cost = (input_tokens / 1000) * self.INPUT_COST_PER_1K
        output_cost = (output_tokens / 1000) * self.OUTPUT_COST_PER_1K
        return round(input_cost + output_cost, 6)

    def track_usage(self, session_id: str, input_tokens: int, output_tokens: int) -> Dict[str, Any]:
        """Track token usage for a session."""
        if session_id not in self._session_tokens:
            self._session_tokens[session_id] = {"input": 0, "output": 0, "requests": 0}

        self._session_tokens[session_id]["input"] += input_tokens
        self._session_tokens[session_id]["output"] += output_tokens
        self._session_tokens[session_id]["requests"] += 1

        usage = self._session_tokens[session_id]
        return {
            "session_input_tokens": usage["input"],
            "session_output_tokens": usage["output"],
            "session_requests": usage["requests"],
            "session_cost": self.estimate_cost(usage["input"], usage["output"])
        }

    def get_session_usage(self, session_id: str) -> Dict[str, Any]:
        """Get current usage for a session."""
        usage = self._session_tokens.get(session_id, {"input": 0, "output": 0, "requests": 0})
        return {
            "input_tokens": usage["input"],
            "output_tokens": usage["output"],
            "requests": usage["requests"],
            "estimated_cost": self.estimate_cost(usage["input"], usage["output"])
        }

    def build_context(
        self,
        session: Dict[str, Any],
        system_prompt: str,
        current_message: str
    ) -> List[Dict[str, str]]:
        """
        Build optimized context for Claude API call.

        Prioritizes:
        1. System prompt (always included)
        2. Original resume (always included)
        3. User corrections (always included)
        4. Recent messages (as many as fit)
        """
        messages = []

        # Calculate available tokens for messages
        system_tokens = self.estimate_tokens(system_prompt)
        resume_tokens = self.estimate_tokens(session.get("resume_text", ""))
        current_msg_tokens = self.estimate_tokens(current_message)

        available_for_history = (
            self.MAX_CONTEXT_TOKENS
            - system_tokens
            - resume_tokens
            - current_msg_tokens
            - 500  # Buffer for corrections and formatting
        )

        # Build resume context with corrections - OPTIMIZED for fewer tokens
        resume_text = session.get("resume_text", "")
        corrections = session.get("corrections", [])

        # Compact corrections format
        corrections_text = ""
        if corrections:
            corrections_text = "\nCORRECTIONS: " + "; ".join(corrections[-5:])

        # Optimized resume framing (~80 tokens vs ~200)
        messages.append({
            "role": "user",
            "content": f"""RESUME (source of truth):
{resume_text}
{corrections_text}
Use ONLY these facts. Never invent details."""
        })

        # Short acknowledgment (~20 tokens vs ~60)
        messages.append({
            "role": "assistant",
            "content": "Understood. I'll only use facts from your resume and corrections. How can I help?"
        })

        # Add conversation history (most recent messages that fit)
        history = session.get("messages", [])

        if history:
            # Take last N messages
            recent_history = history[-self.MAX_MESSAGES_TO_KEEP:]

            # Calculate tokens and trim if needed
            history_tokens = 0
            messages_to_add = []

            for msg in recent_history:
                msg_tokens = msg.get("tokens", self.estimate_tokens(msg.get("content", "")))
                if history_tokens + msg_tokens <= available_for_history:
                    messages_to_add.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })
                    history_tokens += msg_tokens
                else:
                    break

            messages.extend(messages_to_add)

            if len(messages_to_add) < len(recent_history):
                logger.info(f"Trimmed conversation history from {len(recent_history)} to {len(messages_to_add)} messages")

        # Add current message
        messages.append({
            "role": "user",
            "content": current_message
        })

        total_tokens = sum(self.estimate_tokens(m["content"]) for m in messages)
        logger.debug(f"Built context with {len(messages)} messages, ~{total_tokens} tokens")

        return messages

    def should_summarize(self, session: Dict[str, Any]) -> bool:
        """Check if conversation is getting long and should be summarized."""
        return session.get("token_count", 0) > 6000

    def get_summary_prompt(self, messages: List[Dict[str, str]]) -> str:
        """Generate prompt to summarize older messages."""
        conversation = "\n".join(
            f"{m['role'].upper()}: {m['content'][:200]}..."
            for m in messages
        )
        return f"""Summarize the key points from this conversation in 2-3 sentences:

{conversation}

Focus on: what the user wants to achieve, any corrections they made, and key feedback given."""


# Singleton instance
context_manager = ContextManager()
