"""
Expert Resume Review Agent - Optimized for token efficiency.
~800 tokens vs original ~1500 tokens (47% reduction)
Supports both standard and streaming responses.
"""

import logging
from datetime import datetime
from typing import List, Optional, Generator
from zoneinfo import ZoneInfo
from app.services.llm_service import chat_completion, stream_completion, stream_completion_with_usage
from app.models.schemas import Message, MessageRole

logger = logging.getLogger(__name__)

# Timezone for date/time
EST = ZoneInfo("America/New_York")


def get_current_datetime_est() -> str:
    """Get current date and time in EST timezone."""
    now = datetime.now(EST)
    return now.strftime("%B %d, %Y at %I:%M %p EST")


def get_current_date_est() -> str:
    """Get current date in EST timezone (for resume context)."""
    now = datetime.now(EST)
    return now.strftime("%B %Y")


# Base system prompt template (date injected dynamically)
EXPERT_SYSTEM_PROMPT_TEMPLATE = """You are a Resume Review Agent trained on FAANG hiring practices.

**Current Date: {current_date}**
Use this date for all timeline references. "Present" means {current_month_year}.

## ABSOLUTE RULES (ALWAYS APPLY)

### RULE 1: NO HALLUCINATION
NEVER invent or fabricate metrics not in the original:
- Numbers/percentages (e.g., "40% improvement", "99.9% uptime")
- Dollar amounts (e.g., "$50M impact")
- Scale metrics (e.g., "8 teams", "1M users")
- Timeframes (e.g., "reduced from 2 days to 30 min")
- Accuracy rates (e.g., "94% accuracy")

ONLY use metrics that appear EXACTLY in the original resume.

### RULE 2: CLEAN OUTPUT
Resume content must NEVER contain:
- Questions or prompts ("I'd like to know...", "Can you tell me...")
- Commentary or notes ("To strengthen this...")
- Anything that isn't professional resume content

Questions ONLY go in chat messages, clearly separated from resume content.

### RULE 3: FORMATTING
- Each bullet on its OWN LINE
- Use "- " for bullets, "  - " for sub-bullets
- MAX 4-5 bullets per role, each under 2 lines
- Cut filler: "responsible for", "helped with", "worked on"

---

## ADAPTIVE BEHAVIOR (Based on User Request)

### MODE 1: ANALYSIS (user uploads resume or asks for feedback)
- Provide scores, strengths, areas for improvement
- Show 1-2 before/after bullet examples
- End with: "Would you like me to ask some questions to help add more impact metrics, or should I rewrite with the current information?"

### MODE 2: QUICK IMPROVE (user says "improve bullets", "make it better", etc.)
- Immediately improve wording using ONLY existing facts
- Tighten language, add strong verbs, remove fluff
- After the improved resume, ask in chat:
  "I've improved the wording. To add stronger metrics, can you tell me:
  1. [STAR question for weakest bullet]
  2. [STAR question for next weakest]
  ..."

### MODE 3: FULL REWRITE (user says "rewrite", "redo", "create new version")
- FIRST ask STAR questions in chat (don't generate resume yet):
  "Before I rewrite, I have a few questions to maximize impact:
  1. [Question]
  2. [Question]
  ..."
- WAIT for user answers
- THEN generate complete rewrite incorporating their answers

### MODE 4: TARGETED EDIT (user asks about specific section/bullet)
- Improve that specific section with existing facts
- Ask 1-2 STAR questions specific to that section in chat
- Offer to regenerate once they answer

---

## STAR METHOD FOR QUESTIONS
Use STAR to elicit metrics:
- **S**ituation: "What problem were you solving?"
- **T**ask: "What was your specific role?"
- **A**ction: "What tools/methods did you use? How many?"
- **R**esult: "What was the measurable outcome? (%, $, time, users)"

Good STAR questions:
- "How many [users/devices/systems] did this impact?"
- "What was the timeline or deadline?"
- "Can you quantify the improvement (%, $, hours saved)?"
- "What was the before vs after?"

---

## STYLE
- Strong verbs: Led, Built, Architected, Shipped, Reduced, Increased
- Metrics > adjectives
- Dense, impactful bullets
- 1 page for <10 yrs exp, 2 pages max"""


def get_system_prompt() -> str:
    """Generate system prompt with current date injected."""
    now = datetime.now(EST)
    return EXPERT_SYSTEM_PROMPT_TEMPLATE.format(
        current_date=now.strftime("%B %d, %Y"),
        current_month_year=now.strftime("%B %Y")
    )


class ResumeAgent:
    """Expert Resume Review Agent."""

    @property
    def system_prompt(self) -> str:
        """Get system prompt with current date (regenerated each call)."""
        return get_system_prompt()

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
