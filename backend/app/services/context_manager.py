"""
Context window management for Claude API calls.
Optimizes token usage to control costs while maintaining conversation quality.
"""

import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class ContextManager:
    """Manages Claude context window to control costs."""

    # Token limits
    MAX_CONTEXT_TOKENS = 8000  # Leave room for response
    RESUME_TOKEN_ESTIMATE = 1500  # Average resume size
    SYSTEM_PROMPT_TOKENS = 1500  # Approximate system prompt size
    MAX_MESSAGES_TO_KEEP = 10  # Keep last N messages

    def __init__(self):
        pass

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count (rough approximation: 4 chars = 1 token)."""
        return len(text) // 4

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

        # Build resume context with corrections
        resume_text = session.get("resume_text", "")
        corrections = session.get("corrections", [])

        corrections_text = ""
        if corrections:
            corrections_text = "\n\n## USER CORRECTIONS (THESE OVERRIDE THE RESUME):\n" + \
                             "\n".join(f"- {c}" for c in corrections[-5:])  # Last 5 corrections

        # Add resume as first message
        messages.append({
            "role": "user",
            "content": f"""## ORIGINAL RESUME (SOURCE OF TRUTH FOR ALL FACTS):
---
{resume_text}
---
{corrections_text}

IMPORTANT: When improving or rewriting this resume, you MUST use ONLY the facts from this original resume and any user corrections above."""
        })

        # Add acknowledgment
        messages.append({
            "role": "assistant",
            "content": "I understand. I will ONLY use factual information from the original resume you provided and any corrections you give me. I will never invent or hallucinate any details. How can I help you improve your resume today?"
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
