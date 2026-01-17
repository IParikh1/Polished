"""
LLM service for Claude API interactions.
Supports both standard and streaming completions.
"""

import json
import logging
from typing import List, Dict, Optional, Generator, Tuple
from anthropic import Anthropic
from app.core.config import ANTHROPIC_API_KEY, LLM_MODEL, MAX_TOKENS

logger = logging.getLogger(__name__)

client = None
if ANTHROPIC_API_KEY:
    client = Anthropic(api_key=ANTHROPIC_API_KEY)


def chat_completion(
    messages: List[Dict[str, str]],
    system_prompt: str,
    max_tokens: int = MAX_TOKENS
) -> str:
    """Get completion from Claude API."""
    if not client:
        raise ValueError("ANTHROPIC_API_KEY not configured")

    try:
        response = client.messages.create(
            model=LLM_MODEL,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=messages
        )
        return response.content[0].text
    except Exception as e:
        logger.error(f"LLM error: {e}")
        raise


def stream_completion(
    messages: List[Dict[str, str]],
    system_prompt: str,
    max_tokens: int = MAX_TOKENS
) -> Generator[str, None, None]:
    """Stream completion from Claude API."""
    if not client:
        raise ValueError("ANTHROPIC_API_KEY not configured")

    try:
        with client.messages.stream(
            model=LLM_MODEL,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=messages
        ) as stream:
            for text in stream.text_stream:
                yield text
    except Exception as e:
        logger.error(f"LLM streaming error: {e}")
        raise


def stream_completion_with_usage(
    messages: List[Dict[str, str]],
    system_prompt: str,
    max_tokens: int = MAX_TOKENS
) -> Generator[Tuple[str, Optional[Dict]], None, None]:
    """
    Stream completion and yield usage stats at the end.
    Yields: (text_chunk, None) for content, ("", usage_dict) at end.
    """
    if not client:
        raise ValueError("ANTHROPIC_API_KEY not configured")

    try:
        with client.messages.stream(
            model=LLM_MODEL,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=messages
        ) as stream:
            for text in stream.text_stream:
                yield (text, None)

            # Get final message for usage stats
            final_message = stream.get_final_message()
            usage = {
                "input_tokens": final_message.usage.input_tokens,
                "output_tokens": final_message.usage.output_tokens
            }
            yield ("", usage)
    except Exception as e:
        logger.error(f"LLM streaming error: {e}")
        raise


def format_sse(data: str, event: Optional[str] = None) -> str:
    """Format data as Server-Sent Event."""
    message = ""
    if event:
        message += f"event: {event}\n"
    message += f"data: {data}\n\n"
    return message


def format_sse_json(data: Dict, event: Optional[str] = None) -> str:
    """Format JSON data as Server-Sent Event."""
    return format_sse(json.dumps(data), event)
