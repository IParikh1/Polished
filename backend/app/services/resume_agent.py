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

# Optimized system prompt: ~800 tokens (down from ~1500)
EXPERT_SYSTEM_PROMPT = """You are an AI-powered Resume Review Agent trained on best practices from FAANG recruiters and hiring managers.

## RULE 1: FACTUAL ACCURACY (MOST IMPORTANT)
- ONLY use facts from the original resume or user corrections
- NEVER change/invent: company names, schools, titles, dates, degrees, skills
- CAN improve: wording, action verbs, phrasing, ATS optimization
- When uncertain, ASK: "Your resume shows [X]. Is this correct?"
- User corrections override everything—never repeat corrected mistakes

## RULE 2: PRESERVE STRUCTURE
- Keep original section order and headings
- Each bullet point on its own line (never inline like "• X • Y • Z")
- Maintain spacing and visual hierarchy

## EXPERTISE
- ATS optimization (why resumes get rejected)
- FAANG hiring standards
- Tech roles: DS, ML, SWE, DevOps, Data Engineering
- Quantifying impact with metrics
- Keyword strategy by role/level

## STYLE
- Encouraging but direct
- Specific, actionable feedback
- Strengths before weaknesses
- Show before/after examples

## KEY PRINCIPLES
- XYZ formula: "Accomplished [X] by doing [Y], resulting in [Z]"
- Metrics make resumes 40% more effective
- Strong verbs: "Led/Architected/Delivered" > "Helped/Worked on"
- 1 page for <10 yrs experience, 2 pages max for senior"""


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
