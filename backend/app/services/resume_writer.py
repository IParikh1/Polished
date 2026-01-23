"""
Resume Writer Service for Polished Tech Sales Resume Optimization.
Uses Claude LLM to generate optimized, tailored resumes.
"""

import os
import json
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

from .prompts.rewrite import get_rewrite_prompt
from .prompts import get_role_prompt, BASE_TECH_SALES_PROMPT
from .resume_agent import ROLE_CONFIGS, get_role_keywords


class ResumeTemplate(str, Enum):
    """Available resume templates."""
    MODERN = "modern"
    CLASSIC = "classic"
    ATS_FRIENDLY = "ats_friendly"
    EXECUTIVE = "executive"
    MINIMAL = "minimal"


@dataclass
class ResumeSection:
    """Represents a section of a resume."""
    name: str
    content: str
    bullets: Optional[List[str]] = None


@dataclass
class GeneratedResume:
    """Complete generated resume with metadata."""
    full_text: str
    sections: Dict[str, ResumeSection]
    changes_made: List[str]
    keywords_added: List[str]
    suggestions: List[str]
    match_score_improvement: Optional[int] = None
    template: ResumeTemplate = ResumeTemplate.MODERN


class ResumeWriter:
    """
    LLM-powered resume writer for tech sales professionals.

    Uses Claude to generate optimized, role-specific resumes based on:
    - Original resume content
    - Target sales role
    - Job description (if provided)
    - Collected metrics from the user
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the resume writer.

        Args:
            api_key: Anthropic API key. Falls back to ANTHROPIC_API_KEY env var.
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self._client = None

    @property
    def client(self):
        """Lazy-load the Anthropic client."""
        if self._client is None:
            if not HAS_ANTHROPIC:
                raise RuntimeError("anthropic package not installed. Run: pip install anthropic")
            if not self.api_key:
                raise RuntimeError("ANTHROPIC_API_KEY not configured")
            self._client = anthropic.Anthropic(api_key=self.api_key)
        return self._client

    def is_available(self) -> bool:
        """Check if the LLM service is available."""
        return HAS_ANTHROPIC and bool(self.api_key)

    async def generate_resume(
        self,
        resume_text: str,
        target_role: str,
        job_description: Optional[str] = None,
        metrics: Optional[Dict[str, Any]] = None,
        template: ResumeTemplate = ResumeTemplate.MODERN,
        extracted_data: Optional[Dict[str, Any]] = None,
    ) -> GeneratedResume:
        """
        Generate an optimized resume using Claude.

        Args:
            resume_text: Original resume text
            target_role: Target sales role (entry_sdr, sdr, account_executive, etc.)
            job_description: Optional JD to tailor the resume for
            metrics: Collected sales metrics from the user
            template: Resume template style
            extracted_data: Pre-extracted resume data

        Returns:
            GeneratedResume with full text and metadata
        """
        if not self.is_available():
            # Fallback to rule-based generation if LLM not available
            return await self._generate_rule_based(
                resume_text, target_role, job_description, metrics, template, extracted_data
            )

        # Get role-specific keywords
        role_keywords = get_role_keywords(target_role)
        role_config = ROLE_CONFIGS.get(target_role)

        # Format metrics for prompt
        metrics_str = self._format_metrics(metrics) if metrics else "None provided"

        # Build the system prompt
        system_prompt = self._build_system_prompt(target_role, template)

        # Build the user prompt with all context
        user_prompt = get_rewrite_prompt(
            role=role_config.display_name if role_config else target_role,
            job_description=job_description or "Not provided - optimize for general role fit",
            resume_text=resume_text,
            metrics=metrics_str,
            role_specific_keywords=", ".join(role_keywords[:20]),
        )

        # Add formatting instructions
        user_prompt += f"""

## Template Style: {template.value}
{"Use clean, modern formatting with clear section headers." if template == ResumeTemplate.MODERN else ""}
{"Use traditional formatting with standard sections." if template == ResumeTemplate.CLASSIC else ""}
{"Optimize for ATS systems - avoid tables, graphics, use standard headers." if template == ResumeTemplate.ATS_FRIENDLY else ""}
{"Use executive-level formatting with emphasis on leadership and strategic impact." if template == ResumeTemplate.EXECUTIVE else ""}
{"Use minimal, clean design with focus on content clarity." if template == ResumeTemplate.MINIMAL else ""}

Please provide the complete rewritten resume followed by the metadata sections (CHANGES MADE, KEYWORDS ADDED, SUGGESTIONS).
"""

        # Call Claude API
        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                messages=[
                    {"role": "user", "content": user_prompt}
                ],
                system=system_prompt,
            )

            response_text = response.content[0].text

            # Parse the response
            return self._parse_llm_response(response_text, template)

        except Exception as e:
            # Log error and fallback to rule-based
            print(f"LLM generation failed: {e}")
            return await self._generate_rule_based(
                resume_text, target_role, job_description, metrics, template, extracted_data
            )

    async def rewrite_section(
        self,
        section_name: str,
        section_content: str,
        target_role: str,
        context: Optional[str] = None,
        job_description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Rewrite a specific section of a resume.

        Args:
            section_name: Name of section (summary, experience, skills, education)
            section_content: Original section content
            target_role: Target sales role
            context: Additional context for the rewrite
            job_description: Optional JD for tailoring

        Returns:
            Dict with rewritten content and changes
        """
        if not self.is_available():
            return self._rewrite_section_rule_based(
                section_name, section_content, target_role, context
            )

        role_keywords = get_role_keywords(target_role)
        role_config = ROLE_CONFIGS.get(target_role)

        prompt = f"""Rewrite this {section_name} section for a tech sales resume targeting a {role_config.display_name if role_config else target_role} role.

## Original {section_name.title()}:
{section_content}

## Context:
{context or "Optimize for the target role"}

## Job Description:
{job_description or "Not provided"}

## Key Requirements:
1. Maintain factual accuracy - never invent information
2. Use action verbs and quantified achievements
3. Incorporate relevant keywords: {', '.join(role_keywords[:10])}
4. Follow the metrics-first bullet formula for experience
5. Keep formatting clean and ATS-friendly

## Output Format:
Provide the rewritten section, then list specific changes made.

REWRITTEN SECTION:
[Your rewritten content here]

CHANGES MADE:
1. [Change description]
2. [Change description]
"""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2048,
                messages=[{"role": "user", "content": prompt}],
                system=BASE_TECH_SALES_PROMPT,
            )

            response_text = response.content[0].text

            # Parse response
            parts = response_text.split("CHANGES MADE:")
            rewritten = parts[0].replace("REWRITTEN SECTION:", "").strip()
            changes = []

            if len(parts) > 1:
                changes_text = parts[1].strip()
                changes = [
                    line.strip().lstrip("0123456789.-) ")
                    for line in changes_text.split("\n")
                    if line.strip() and not line.strip().startswith("#")
                ]

            return {
                "section": section_name,
                "original": section_content,
                "rewritten": rewritten,
                "changes": changes[:10],
                "improvement_score": self._calculate_improvement(section_content, rewritten),
            }

        except Exception as e:
            print(f"Section rewrite failed: {e}")
            return self._rewrite_section_rule_based(
                section_name, section_content, target_role, context
            )

    async def generate_summary(
        self,
        extracted_data: Dict[str, Any],
        target_role: str,
        job_description: Optional[str] = None,
        tone: str = "professional",
    ) -> Dict[str, str]:
        """
        Generate a professional summary for a resume.

        Args:
            extracted_data: Extracted resume data (name, skills, experience, etc.)
            target_role: Target sales role
            job_description: Optional JD for tailoring
            tone: Tone of the summary (professional, confident, dynamic)

        Returns:
            Dict with generated summary and variants
        """
        role_config = ROLE_CONFIGS.get(target_role)
        role_keywords = get_role_keywords(target_role)

        name = extracted_data.get("name", "")
        years = extracted_data.get("years_of_experience", 0)
        skills = extracted_data.get("skills", [])[:8]

        if not self.is_available():
            # Rule-based summary generation
            return self._generate_summary_rule_based(
                name, years, skills, target_role, role_config, tone
            )

        prompt = f"""Generate a compelling professional summary for a tech sales resume.

## Candidate Profile:
- Name: {name}
- Years of Experience: {years}
- Key Skills: {', '.join(skills)}
- Target Role: {role_config.display_name if role_config else target_role}

## Job Description (if targeting specific role):
{job_description or "Not provided - generate general summary"}

## Key Keywords to Consider:
{', '.join(role_keywords[:15])}

## Tone: {tone}

## Requirements:
1. 2-3 sentences maximum
2. Lead with strongest quantified achievement if possible
3. Highlight relevant experience level
4. Include 2-3 key skills/strengths
5. End with value proposition
6. NO generic phrases like "seeking opportunity" or "passionate professional"

Generate 3 variants:
1. STANDARD: Professional and balanced
2. CONFIDENT: Bold, achievement-focused
3. DYNAMIC: Energetic, growth-oriented

Format:
STANDARD:
[summary text]

CONFIDENT:
[summary text]

DYNAMIC:
[summary text]
"""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
                system="You are an expert resume writer specializing in tech sales roles.",
            )

            response_text = response.content[0].text

            # Parse variants
            summaries = {}
            current_key = None
            current_text = []

            for line in response_text.split("\n"):
                line = line.strip()
                if line.upper().startswith("STANDARD:"):
                    if current_key:
                        summaries[current_key] = " ".join(current_text).strip()
                    current_key = "standard"
                    current_text = [line.replace("STANDARD:", "").strip()]
                elif line.upper().startswith("CONFIDENT:"):
                    if current_key:
                        summaries[current_key] = " ".join(current_text).strip()
                    current_key = "confident"
                    current_text = [line.replace("CONFIDENT:", "").strip()]
                elif line.upper().startswith("DYNAMIC:"):
                    if current_key:
                        summaries[current_key] = " ".join(current_text).strip()
                    current_key = "dynamic"
                    current_text = [line.replace("DYNAMIC:", "").strip()]
                elif current_key and line:
                    current_text.append(line)

            if current_key:
                summaries[current_key] = " ".join(current_text).strip()

            # Ensure we have at least the standard summary
            if "standard" not in summaries:
                summaries["standard"] = self._generate_summary_rule_based(
                    name, years, skills, target_role, role_config, tone
                )["standard"]

            return summaries

        except Exception as e:
            print(f"Summary generation failed: {e}")
            return self._generate_summary_rule_based(
                name, years, skills, target_role, role_config, tone
            )

    async def enhance_bullets(
        self,
        bullets: List[str],
        target_role: str,
        company_context: Optional[str] = None,
    ) -> List[Dict[str, str]]:
        """
        Enhance experience bullet points with metrics and impact.

        Args:
            bullets: Original bullet points
            target_role: Target sales role
            company_context: Context about the company/role

        Returns:
            List of dicts with original and enhanced bullets
        """
        role_config = ROLE_CONFIGS.get(target_role)
        metrics_keywords = role_config.metrics_keywords if role_config else []

        if not self.is_available():
            return [{"original": b, "enhanced": b, "needs_metrics": True} for b in bullets]

        prompt = f"""Enhance these experience bullet points for a {role_config.display_name if role_config else target_role} resume.

## Original Bullets:
{chr(10).join(f"- {b}" for b in bullets)}

## Company Context:
{company_context or "Not provided"}

## Target Metrics to Highlight:
{', '.join(metrics_keywords)}

## Enhancement Rules:
1. Lead with quantified results (%, $, #)
2. Use format: "Achieved [X] by [action], resulting in [impact]"
3. If no metrics available, restructure for impact
4. Keep factual - add [NEEDS METRIC] placeholder where data is needed
5. Use strong action verbs

For each bullet, provide:
ORIGINAL: [original text]
ENHANCED: [enhanced text]
NEEDS_METRICS: [true/false - if placeholder added]

---
"""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2048,
                messages=[{"role": "user", "content": prompt}],
                system="You are an expert resume writer. Enhance bullets while maintaining factual accuracy.",
            )

            response_text = response.content[0].text

            # Parse enhanced bullets
            enhanced = []
            current = {}

            for line in response_text.split("\n"):
                line = line.strip()
                if line.startswith("ORIGINAL:"):
                    if current:
                        enhanced.append(current)
                    current = {"original": line.replace("ORIGINAL:", "").strip()}
                elif line.startswith("ENHANCED:"):
                    current["enhanced"] = line.replace("ENHANCED:", "").strip()
                elif line.startswith("NEEDS_METRICS:"):
                    current["needs_metrics"] = "true" in line.lower()

            if current:
                enhanced.append(current)

            # Fill in any missing bullets
            for i, bullet in enumerate(bullets):
                if i >= len(enhanced):
                    enhanced.append({
                        "original": bullet,
                        "enhanced": bullet,
                        "needs_metrics": True
                    })

            return enhanced

        except Exception as e:
            print(f"Bullet enhancement failed: {e}")
            return [{"original": b, "enhanced": b, "needs_metrics": True} for b in bullets]

    def _build_system_prompt(self, target_role: str, template: ResumeTemplate) -> str:
        """Build the system prompt for resume generation."""
        base = BASE_TECH_SALES_PROMPT
        role_prompt = get_role_prompt(target_role)

        system = f"""{base}

{role_prompt if role_prompt else ""}

## Resume Writing Guidelines

You are generating a complete, polished resume. Follow these rules:

1. **Structure**: Contact → Summary → Experience → Education → Skills
2. **Formatting**: Clean, professional, ATS-compatible
3. **Accuracy**: NEVER invent facts, dates, companies, or metrics
4. **Metrics First**: Lead bullets with quantified results
5. **Keywords**: Naturally incorporate role-specific keywords
6. **Length**: 1 page for <7 years experience, max 2 pages for senior roles

Template: {template.value}
"""
        return system

    def _format_metrics(self, metrics: Dict[str, Any]) -> str:
        """Format collected metrics for the prompt."""
        if not metrics:
            return "None provided"

        formatted = []
        for company, data in metrics.items():
            if isinstance(data, dict):
                company_metrics = []
                for key, value in data.items():
                    if value:
                        company_metrics.append(f"  - {key}: {value}")
                if company_metrics:
                    formatted.append(f"{company}:\n" + "\n".join(company_metrics))
            else:
                formatted.append(f"{company}: {data}")

        return "\n".join(formatted) if formatted else "None provided"

    def _parse_llm_response(self, response_text: str, template: ResumeTemplate) -> GeneratedResume:
        """Parse the LLM response into a GeneratedResume object."""
        # Split into main resume and metadata
        parts = re.split(r"\*\*CHANGES MADE:\*\*|CHANGES MADE:", response_text, flags=re.IGNORECASE)

        resume_text = parts[0].strip()

        changes = []
        keywords = []
        suggestions = []

        if len(parts) > 1:
            metadata = parts[1]

            # Extract changes
            changes_match = re.findall(r"^\d+\.\s*(.+)$", metadata, re.MULTILINE)
            changes = changes_match[:10]

            # Extract keywords section
            keywords_section = re.search(
                r"\*\*KEYWORDS ADDED:\*\*|KEYWORDS ADDED:(.*?)(?:\*\*SUGGESTIONS|\Z)",
                metadata,
                re.IGNORECASE | re.DOTALL
            )
            if keywords_section:
                kw_text = keywords_section.group(1) if keywords_section.group(1) else ""
                keywords = [
                    line.strip().lstrip("- ")
                    for line in kw_text.split("\n")
                    if line.strip() and line.strip().startswith("-")
                ][:15]

            # Extract suggestions
            suggestions_section = re.search(
                r"\*\*SUGGESTIONS.*?:\*\*|SUGGESTIONS.*?:(.*?)$",
                metadata,
                re.IGNORECASE | re.DOTALL
            )
            if suggestions_section:
                sugg_text = suggestions_section.group(1) if suggestions_section.group(1) else ""
                suggestions = [
                    line.strip().lstrip("- ")
                    for line in sugg_text.split("\n")
                    if line.strip() and line.strip().startswith("-")
                ][:5]

        # Parse sections from resume text
        sections = self._parse_resume_sections(resume_text)

        return GeneratedResume(
            full_text=resume_text,
            sections=sections,
            changes_made=changes,
            keywords_added=keywords,
            suggestions=suggestions,
            template=template,
        )

    def _parse_resume_sections(self, resume_text: str) -> Dict[str, ResumeSection]:
        """Parse resume text into sections."""
        sections = {}

        # Common section headers
        section_patterns = [
            (r"(?:^|\n)(?:SUMMARY|PROFESSIONAL SUMMARY|PROFILE)[:\s]*\n?(.*?)(?=\n(?:EXPERIENCE|WORK|EDUCATION|SKILLS)|$)", "summary"),
            (r"(?:^|\n)(?:EXPERIENCE|WORK EXPERIENCE|PROFESSIONAL EXPERIENCE)[:\s]*\n?(.*?)(?=\n(?:EDUCATION|SKILLS|CERTIFICATIONS)|$)", "experience"),
            (r"(?:^|\n)(?:EDUCATION|ACADEMIC)[:\s]*\n?(.*?)(?=\n(?:SKILLS|CERTIFICATIONS|$)|$)", "education"),
            (r"(?:^|\n)(?:SKILLS|TECHNICAL SKILLS|CORE COMPETENCIES)[:\s]*\n?(.*?)(?=\n(?:CERTIFICATIONS|$)|$)", "skills"),
        ]

        for pattern, name in section_patterns:
            match = re.search(pattern, resume_text, re.IGNORECASE | re.DOTALL)
            if match:
                content = match.group(1).strip()
                bullets = [
                    line.strip().lstrip("•-* ")
                    for line in content.split("\n")
                    if line.strip().startswith(("•", "-", "*", "–"))
                ]
                sections[name] = ResumeSection(
                    name=name,
                    content=content,
                    bullets=bullets if bullets else None,
                )

        return sections

    async def _generate_rule_based(
        self,
        resume_text: str,
        target_role: str,
        job_description: Optional[str],
        metrics: Optional[Dict[str, Any]],
        template: ResumeTemplate,
        extracted_data: Optional[Dict[str, Any]],
    ) -> GeneratedResume:
        """Fallback rule-based resume generation."""
        data = extracted_data or {}
        role_config = ROLE_CONFIGS.get(target_role)

        # Build sections
        sections = {}
        changes = []
        keywords_added = []
        suggestions = []

        # Summary section
        name = data.get("name", "")
        years = data.get("years_of_experience", 0)
        skills = data.get("skills", [])[:5]

        summary_text = (
            f"Results-driven {role_config.display_name if role_config else 'sales professional'} "
            f"with {years}+ years of experience. "
            f"Expertise in {', '.join(skills[:3]) if skills else 'B2B sales'}. "
            f"Proven track record of exceeding targets and building strong client relationships."
        )
        sections["summary"] = ResumeSection(name="summary", content=summary_text)
        changes.append("Generated professional summary")

        # Add keywords from role config
        if role_config:
            keywords_added = role_config.keywords[:10]

        # Generate suggestions
        suggestions = [
            "Add specific quota attainment percentages",
            "Include deal sizes and sales cycle information",
            f"Highlight {role_config.display_name if role_config else 'role'}-specific achievements",
        ]

        return GeneratedResume(
            full_text=resume_text,  # Return original with suggested changes
            sections=sections,
            changes_made=changes,
            keywords_added=keywords_added,
            suggestions=suggestions,
            template=template,
        )

    def _rewrite_section_rule_based(
        self,
        section_name: str,
        section_content: str,
        target_role: str,
        context: Optional[str],
    ) -> Dict[str, Any]:
        """Fallback rule-based section rewrite."""
        role_config = ROLE_CONFIGS.get(target_role)

        # Simple improvements
        improved = section_content
        changes = []

        if section_name == "summary":
            if not improved.strip():
                improved = f"Experienced {role_config.display_name if role_config else 'sales professional'} with a track record of success."
                changes.append("Added professional summary")
        elif section_name == "skills":
            if role_config:
                # Add missing keywords
                for kw in role_config.keywords[:5]:
                    if kw.lower() not in improved.lower():
                        improved += f", {kw}"
                        changes.append(f"Added keyword: {kw}")

        return {
            "section": section_name,
            "original": section_content,
            "rewritten": improved.strip(", "),
            "changes": changes,
            "improvement_score": len(changes) * 10,
        }

    def _generate_summary_rule_based(
        self,
        name: str,
        years: int,
        skills: List[str],
        target_role: str,
        role_config: Any,
        tone: str,
    ) -> Dict[str, str]:
        """Generate summary variants using rules."""
        role_name = role_config.display_name if role_config else target_role
        skill_str = ", ".join(skills[:3]) if skills else "sales and business development"

        standard = (
            f"Experienced {role_name.lower()} with {years}+ years in tech sales. "
            f"Skilled in {skill_str}. Committed to driving revenue growth and exceeding targets."
        )

        confident = (
            f"Top-performing {role_name.lower()} with {years}+ years of consistently exceeding quota. "
            f"Expert in {skill_str}, with a proven ability to close enterprise deals and drive significant revenue."
        )

        dynamic = (
            f"High-energy {role_name.lower()} bringing {years}+ years of sales excellence. "
            f"Known for {skill_str} and building lasting client relationships that fuel growth."
        )

        return {
            "standard": standard,
            "confident": confident,
            "dynamic": dynamic,
        }

    def _calculate_improvement(self, original: str, improved: str) -> int:
        """Calculate improvement score between original and improved text."""
        if original == improved:
            return 0

        score = 0

        # Length improvement (more detail is often better)
        if len(improved) > len(original):
            score += min((len(improved) - len(original)) // 10, 20)

        # Check for action verbs
        action_verbs = ["achieved", "exceeded", "generated", "closed", "led", "delivered", "drove"]
        for verb in action_verbs:
            if verb in improved.lower() and verb not in original.lower():
                score += 10

        # Check for metrics
        if re.search(r'\d+%|\$[\d,]+|\d+\+', improved) and not re.search(r'\d+%|\$[\d,]+|\d+\+', original):
            score += 20

        return min(score, 100)


# Singleton instance
_resume_writer: Optional[ResumeWriter] = None


def get_writer(api_key: Optional[str] = None) -> ResumeWriter:
    """Get the resume writer singleton."""
    global _resume_writer
    if _resume_writer is None:
        _resume_writer = ResumeWriter(api_key)
    return _resume_writer


async def generate_resume(
    resume_text: str,
    target_role: str,
    job_description: Optional[str] = None,
    metrics: Optional[Dict[str, Any]] = None,
    template: str = "modern",
    extracted_data: Optional[Dict[str, Any]] = None,
) -> GeneratedResume:
    """Convenience function to generate a resume."""
    writer = get_writer()
    return await writer.generate_resume(
        resume_text=resume_text,
        target_role=target_role,
        job_description=job_description,
        metrics=metrics,
        template=ResumeTemplate(template),
        extracted_data=extracted_data,
    )
