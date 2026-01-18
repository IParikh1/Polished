"""
Expert Resume Review Agent - Optimized for token efficiency.
~800 tokens vs original ~1500 tokens (47% reduction)
Supports both standard and streaming responses.
"""

import logging
from typing import List, Optional, Generator
from app.services.llm_service import chat_completion, stream_completion, stream_completion_with_usage
from app.models.schemas import Message, MessageRole

logger = logging.getLogger(__name__)

# Optimized system prompt for concise, ATS-optimized resumes
EXPERT_SYSTEM_PROMPT = """You are a Resume Review Agent trained on FAANG hiring practices.

## CRITICAL RULES
1. FACTUAL ACCURACY: Only use facts from the resume. Never invent companies, titles, dates, degrees, or skills.
2. CONCISENESS: Every word must earn its place. No filler, fluff, or redundant phrases.
3. LENGTH: 1 page for <10 yrs experience, 2 pages max. Never exceed this.

## FORMATTING (STRICT)
- Each bullet point on its OWN LINE with proper markdown
- Use "- " for bullets, "  - " (2 spaces) for sub-bullets
- Never inline bullets like "• X • Y • Z"
- Keep consistent spacing between sections

## RESUME REWRITE RULES
When rewriting a resume:
- BE CONCISE: Cut adjectives, adverbs, and filler words ruthlessly
- NO FLUFF: Remove phrases like "responsible for", "helped with", "worked on"
- DENSE IMPACT: Pack metrics and achievements into tight, punchy bullets
- ATS KEYWORDS: Include role-relevant keywords naturally, not stuffed
- XYZ FORMAT: "[Action verb] [what] by [how], resulting in [metric]"
- MAX 4-5 bullets per role, each under 2 lines
- Prioritize quantifiable achievements over job duties

## GOOD vs BAD
BAD: "Responsible for helping the team work on developing and implementing new features for the platform"
GOOD: "Built 5 platform features, increasing user engagement 23%"

BAD: "Successfully managed and coordinated with cross-functional teams to deliver projects on time"
GOOD: "Led 3 cross-functional teams; delivered all projects on schedule"

## STYLE
- Direct and specific
- Metrics > adjectives
- Strong verbs: Led, Built, Shipped, Reduced, Increased, Architected"""


class ResumeAgent:
    """Expert Resume Review Agent."""

    def __init__(self):
        self.system_prompt = EXPERT_SYSTEM_PROMPT

    def analyze_resume(self, resume_text: str) -> str:
        """Provide initial comprehensive analysis of a resume."""
        # Optimized prompt: ~100 tokens (down from ~150)
        messages = [
            {
                "role": "user",
                "content": f"""Analyze this resume:

{resume_text}

Provide: 1) Overall score (1-10) 2) ATS score (1-10) 3) Top 3 strengths 4) Top 3 improvements 5) Target companies 6) One bullet rewrite (before/after)"""
            }
        ]

        return chat_completion(messages, self.system_prompt)

    def chat(self, user_message: str, conversation_history: List[Message], resume_text: Optional[str] = None, user_corrections: Optional[List[str]] = None) -> str:
        """Continue conversation with the user."""
        messages = []

        # Optimized context: ~80 tokens for framing (down from ~200)
        if resume_text:
            corrections_text = ""
            if user_corrections:
                corrections_text = "\nCORRECTIONS: " + "; ".join(user_corrections[-5:])  # Last 5 only

            messages.append({
                "role": "user",
                "content": f"""RESUME (source of truth):
{resume_text}
{corrections_text}
Use ONLY these facts. Never invent details."""
            })
            messages.append({
                "role": "assistant",
                "content": "Understood. I'll only use facts from your resume and corrections. How can I help?"
            })

        # Add conversation history
        for msg in conversation_history:
            messages.append({
                "role": msg.role.value,
                "content": msg.content
            })

        # Add current message
        messages.append({
            "role": "user",
            "content": user_message
        })

        return chat_completion(messages, self.system_prompt)

    def suggest_improvements(self, resume_text: str, target_role: str, target_company: Optional[str] = None) -> str:
        """Suggest specific improvements for a target role."""
        # Optimized prompt: ~80 tokens (down from ~150)
        company_context = f" at {target_company}" if target_company else ""

        messages = [
            {
                "role": "user",
                "content": f"""Resume:
{resume_text}

Target: {target_role}{company_context}

Provide: 1) Match score (1-10) 2) 5 specific changes 3) Keywords to add 4) What to emphasize 5) What to de-emphasize 6) Best bullet rewritten for this role"""
            }
        ]

        return chat_completion(messages, self.system_prompt)

    def rewrite_section(self, section_text: str, section_type: str, context: str = "") -> str:
        """Rewrite a specific section of the resume."""
        # Optimized prompt: ~50 tokens (down from ~100)
        ctx = f" Context: {context}" if context else ""
        messages = [
            {
                "role": "user",
                "content": f"""Rewrite this {section_type} section:

{section_text}
{ctx}
Show: 1) Improved version 2) What changed and why"""
            }
        ]

        return chat_completion(messages, self.system_prompt)

    # =========================================================================
    # STREAMING METHODS
    # =========================================================================

    def analyze_resume_stream(self, resume_text: str) -> Generator[str, None, None]:
        """Stream initial resume analysis."""
        messages = [
            {
                "role": "user",
                "content": f"""Analyze this resume:

{resume_text}

Provide: 1) Overall score (1-10) 2) ATS score (1-10) 3) Top 3 strengths 4) Top 3 improvements 5) Target companies 6) One bullet rewrite (before/after)"""
            }
        ]

        yield from stream_completion(messages, self.system_prompt)

    def chat_stream(
        self,
        user_message: str,
        conversation_history: List[Message],
        resume_text: Optional[str] = None,
        user_corrections: Optional[List[str]] = None
    ) -> Generator[str, None, None]:
        """Stream chat response."""
        messages = []

        if resume_text:
            corrections_text = ""
            if user_corrections:
                corrections_text = "\nCORRECTIONS: " + "; ".join(user_corrections[-5:])

            messages.append({
                "role": "user",
                "content": f"""RESUME (source of truth):
{resume_text}
{corrections_text}
Use ONLY these facts. Never invent details."""
            })
            messages.append({
                "role": "assistant",
                "content": "Understood. I'll only use facts from your resume and corrections. How can I help?"
            })

        for msg in conversation_history:
            messages.append({
                "role": msg.role.value,
                "content": msg.content
            })

        messages.append({
            "role": "user",
            "content": user_message
        })

        yield from stream_completion(messages, self.system_prompt)

    def chat_stream_with_usage(
        self,
        user_message: str,
        conversation_history: List[Message],
        resume_text: Optional[str] = None,
        user_corrections: Optional[List[str]] = None
    ) -> Generator[tuple, None, None]:
        """Stream chat response with usage stats at end."""
        messages = []

        if resume_text:
            corrections_text = ""
            if user_corrections:
                corrections_text = "\nCORRECTIONS: " + "; ".join(user_corrections[-5:])

            messages.append({
                "role": "user",
                "content": f"""RESUME (source of truth):
{resume_text}
{corrections_text}
Use ONLY these facts. Never invent details."""
            })
            messages.append({
                "role": "assistant",
                "content": "Understood. I'll only use facts from your resume and corrections. How can I help?"
            })

        for msg in conversation_history:
            messages.append({
                "role": msg.role.value,
                "content": msg.content
            })

        messages.append({
            "role": "user",
            "content": user_message
        })

        yield from stream_completion_with_usage(messages, self.system_prompt)

    def suggest_improvements_stream(
        self,
        resume_text: str,
        target_role: str,
        target_company: Optional[str] = None
    ) -> Generator[str, None, None]:
        """Stream improvement suggestions."""
        company_context = f" at {target_company}" if target_company else ""

        messages = [
            {
                "role": "user",
                "content": f"""Resume:
{resume_text}

Target: {target_role}{company_context}

Provide: 1) Match score (1-10) 2) 5 specific changes 3) Keywords to add 4) What to emphasize 5) What to de-emphasize 6) Best bullet rewritten for this role"""
            }
        ]

        yield from stream_completion(messages, self.system_prompt)


# Singleton instance
resume_agent = ResumeAgent()
