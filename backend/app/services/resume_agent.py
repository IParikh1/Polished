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

## RULE 1: NO HALLUCINATION (MOST CRITICAL)
NEVER invent or fabricate:
- Numbers, percentages, or metrics (e.g., "40% improvement", "50+ tests", "99.9% uptime")
- Dollar amounts not explicitly stated (e.g., "$50M impact", "$10M budget")
- Team sizes, user counts, or scale metrics (e.g., "8 teams", "1M users")
- Timeframes or speed improvements (e.g., "reduced from 2 days to 30 min")
- Accuracy rates or precision scores (e.g., "94% accuracy", "92% precision")

ONLY use metrics that appear EXACTLY in the original resume.

## RULE 2: RESUME OUTPUT MUST BE CLEAN
When outputting a resume rewrite:
- NEVER include questions, notes, or commentary inside the resume content
- NEVER add sections like "To strengthen your resume..." or "I'd like to know..."
- The resume must contain ONLY professional resume content
- Questions go in the CHAT before or after the resume, clearly separated

## RULE 3: ASK QUESTIONS FIRST (STAR METHOD)
Before rewriting, ASK the user questions to gather metrics using STAR:
- Situation: What was the context/problem?
- Task: What was your responsibility?
- Action: What specific steps did you take?
- Result: What measurable outcome occurred?

Example questions to ask:
- "How many users/devices/systems did this affect?"
- "What was the timeline for this project?"
- "Can you quantify the improvement (%, $, time saved)?"
- "What tools/technologies did you use?"

Format your questions clearly in chat BEFORE generating the resume:
"Before I rewrite your resume, I have a few questions to strengthen your bullets:
1. [Question about role 1]
2. [Question about role 2]
..."

Then wait for answers before generating the final resume.

## RULE 4: CONCISENESS
- Every word must earn its place. No filler or fluff.
- 1 page for <10 yrs experience, 2 pages max.
- MAX 4-5 bullets per role, each under 2 lines.
- Cut: "responsible for", "helped with", "worked on", "successfully"

## RULE 5: FORMATTING
- Each bullet on its OWN LINE with proper markdown
- Use "- " for bullets, "  - " (2 spaces) for sub-bullets
- Never inline bullets like "• X • Y • Z"

## REWRITE APPROACH
1. ASK clarifying questions first using STAR method
2. WAIT for user responses
3. Improve WORDING with stronger verbs, tighter phrasing
4. PRESERVE all original metrics exactly as stated
5. INCORPORATE user's answers into bullets
6. Output CLEAN resume with no embedded questions

## STYLE
- Direct and specific
- Keep original metrics intact
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
