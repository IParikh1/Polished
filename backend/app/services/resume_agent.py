"""
Resume Agent Service for Polished Tech Sales Resume Optimization.
Provides role-aware resume analysis using tech sales specific prompts.
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum

from .prompts import (
    BASE_TECH_SALES_PROMPT,
    get_role_prompt,
    ROLE_PROMPTS,
    JD_MATCHING_PROMPT,
    METRICS_EXTRACTION_PROMPT,
)
from .prompts.role_prompts import ROLE_DISPLAY_NAMES


class SalesRole(str, Enum):
    """Target sales role for resume optimization."""
    ENTRY_SDR = "entry_sdr"
    SDR = "sdr"
    ACCOUNT_EXECUTIVE = "account_executive"
    SENIOR_AE = "senior_ae"
    ACCOUNT_MANAGER = "account_manager"
    SALES_MANAGER = "sales_manager"


@dataclass
class RoleConfig:
    """Configuration for a specific sales role."""
    role: SalesRole
    display_name: str
    keywords: List[str]
    metrics_keywords: List[str]
    experience_range: tuple  # (min_years, max_years)
    scoring_weights: Dict[str, float]


# Role-specific configurations
ROLE_CONFIGS: Dict[str, RoleConfig] = {
    "entry_sdr": RoleConfig(
        role=SalesRole.ENTRY_SDR,
        display_name="Entry-Level SDR (0-1 years)",
        keywords=[
            "cold calling", "outbound", "prospecting", "lead generation",
            "crm", "salesforce", "hubspot", "email", "linkedin",
            "communication", "customer service", "competitive", "goal-oriented",
            "coachable", "fast learner", "driven", "resilience",
        ],
        metrics_keywords=[
            "calls", "emails", "meetings booked", "quota", "ramp time",
        ],
        experience_range=(0, 1),
        scoring_weights={
            "transferable_skills": 0.30,
            "communication": 0.25,
            "drive_indicators": 0.20,
            "education": 0.15,
            "formatting": 0.10,
        }
    ),
    "sdr": RoleConfig(
        role=SalesRole.SDR,
        display_name="SDR/BDR (1-3 years)",
        keywords=[
            "sdr", "bdr", "outbound", "prospecting", "cold calling",
            "meetings booked", "sql", "pipeline", "quota attainment",
            "salesforce", "outreach", "salesloft", "zoominfo", "linkedin sales navigator",
            "gong", "chorus", "sequences", "cadence",
        ],
        metrics_keywords=[
            "quota", "meetings booked", "sqls", "calls per day", "emails",
            "conversion rate", "pipeline generated", "ramp time", "ranking",
        ],
        experience_range=(1, 3),
        scoring_weights={
            "quota_attainment": 0.30,
            "activity_metrics": 0.25,
            "tools_experience": 0.20,
            "communication": 0.15,
            "formatting": 0.10,
        }
    ),
    "account_executive": RoleConfig(
        role=SalesRole.ACCOUNT_EXECUTIVE,
        display_name="Account Executive (2-5 years)",
        keywords=[
            "account executive", "ae", "quota", "closed won", "pipeline",
            "full cycle", "discovery", "demo", "negotiation", "closing",
            "acv", "arv", "deal size", "win rate", "sales cycle",
            "meddic", "bant", "challenger", "spin", "sandler",
            "salesforce", "clari", "forecasting",
        ],
        metrics_keywords=[
            "quota attainment", "deals closed", "acv", "revenue",
            "win rate", "sales cycle", "pipeline", "self-sourced",
        ],
        experience_range=(2, 5),
        scoring_weights={
            "quota_attainment": 0.35,
            "deal_metrics": 0.25,
            "methodology": 0.15,
            "tools_experience": 0.15,
            "formatting": 0.10,
        }
    ),
    "senior_ae": RoleConfig(
        role=SalesRole.SENIOR_AE,
        display_name="Senior/Enterprise AE (5+ years)",
        keywords=[
            "enterprise", "strategic", "c-suite", "executive", "complex sales",
            "multi-stakeholder", "land and expand", "fortune 500", "fortune 1000",
            "large deals", "long cycle", "meddpicc", "value selling",
            "business case", "roi", "procurement", "legal", "security review",
            "multi-year", "expansion", "upsell",
        ],
        metrics_keywords=[
            "largest deal", "enterprise deals", "multi-stakeholder",
            "land and expand", "strategic accounts", "fortune", "c-suite",
        ],
        experience_range=(5, 15),
        scoring_weights={
            "deal_complexity": 0.30,
            "strategic_selling": 0.25,
            "quota_attainment": 0.20,
            "executive_presence": 0.15,
            "formatting": 0.10,
        }
    ),
    "account_manager": RoleConfig(
        role=SalesRole.ACCOUNT_MANAGER,
        display_name="Account Manager / CSM",
        keywords=[
            "account manager", "customer success", "csm", "retention",
            "nrr", "grr", "churn", "upsell", "cross-sell", "expansion",
            "renewal", "qbr", "ebr", "customer satisfaction", "nps", "csat",
            "book of business", "arr managed", "logo retention",
        ],
        metrics_keywords=[
            "nrr", "grr", "churn rate", "expansion revenue",
            "book of business", "arr", "renewal rate", "logo retention",
        ],
        experience_range=(2, 10),
        scoring_weights={
            "retention_metrics": 0.35,
            "expansion_revenue": 0.25,
            "customer_relationship": 0.20,
            "strategic_planning": 0.10,
            "formatting": 0.10,
        }
    ),
    "sales_manager": RoleConfig(
        role=SalesRole.SALES_MANAGER,
        display_name="Sales Manager / Director",
        keywords=[
            "sales manager", "sales director", "team lead", "leadership",
            "hiring", "coaching", "mentoring", "team quota", "rep productivity",
            "forecast", "territory", "go-to-market", "sales operations",
            "process improvement", "onboarding", "ramp", "retention",
        ],
        metrics_keywords=[
            "team quota", "team size", "revenue responsibility",
            "rep retention", "promotions", "ramp time", "win rate improvement",
        ],
        experience_range=(5, 20),
        scoring_weights={
            "team_performance": 0.30,
            "leadership_indicators": 0.25,
            "hiring_development": 0.20,
            "process_improvement": 0.15,
            "formatting": 0.10,
        }
    ),
}


class ResumeAgent:
    """
    Role-aware resume analysis agent for tech sales professionals.

    Uses specialized prompts and scoring based on the target sales role.
    """

    def __init__(self):
        self._llm_client: Optional[Callable] = None

    def set_llm_client(self, client: Callable) -> None:
        """
        Set the LLM client for AI-powered analysis.

        Args:
            client: Async callable that takes (system_prompt, user_message) and returns response
        """
        self._llm_client = client

    def get_system_prompt(
        self,
        role: Optional[str] = None,
        include_jd_matching: bool = False,
        include_metrics_extraction: bool = False,
    ) -> str:
        """
        Construct the full system prompt based on role and context.

        Args:
            role: Target sales role (e.g., 'entry_sdr', 'account_executive')
            include_jd_matching: Include JD matching instructions
            include_metrics_extraction: Include metrics extraction instructions

        Returns:
            Complete system prompt string
        """
        prompt = BASE_TECH_SALES_PROMPT

        if role and role in ROLE_PROMPTS:
            role_prompt = get_role_prompt(role)
            if role_prompt:
                prompt += "\n\n" + role_prompt

        if include_jd_matching:
            prompt += "\n\n" + JD_MATCHING_PROMPT

        if include_metrics_extraction:
            prompt += "\n\n" + METRICS_EXTRACTION_PROMPT

        return prompt

    def get_role_config(self, role: str) -> Optional[RoleConfig]:
        """Get configuration for a specific role."""
        return ROLE_CONFIGS.get(role)

    def get_role_keywords(self, role: str) -> List[str]:
        """Get keywords relevant to a specific role."""
        config = ROLE_CONFIGS.get(role)
        if config:
            return config.keywords + config.metrics_keywords
        return []

    def get_all_roles(self) -> List[Dict[str, str]]:
        """Get all available roles with display names."""
        return [
            {"id": role_id, "name": config.display_name}
            for role_id, config in ROLE_CONFIGS.items()
        ]

    async def analyze_resume(
        self,
        resume_text: str,
        target_role: Optional[str] = None,
        extracted_data: Optional[Dict[str, Any]] = None,
        job_description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Analyze a resume for a specific sales role.

        Args:
            resume_text: Raw resume text
            target_role: Target sales role
            extracted_data: Pre-extracted structured data
            job_description: Optional JD for matching

        Returns:
            Analysis results including scores and recommendations
        """
        extracted = extracted_data or {}
        text_lower = resume_text.lower()

        # Get role configuration
        role_config = ROLE_CONFIGS.get(target_role) if target_role else None

        # Calculate role-specific scores
        scores = self._calculate_role_scores(text_lower, extracted, role_config)

        # Find matching and missing keywords
        keyword_analysis = self._analyze_keywords(text_lower, role_config)

        # Analyze metrics presence
        metrics_analysis = self._analyze_metrics(text_lower, extracted, role_config)

        # Generate recommendations
        recommendations = self._generate_recommendations(
            scores, keyword_analysis, metrics_analysis, role_config
        )

        result = {
            "target_role": target_role,
            "role_display_name": role_config.display_name if role_config else "General",
            "scores": scores,
            "overall_score": scores.get("overall", 0),
            "keyword_analysis": keyword_analysis,
            "metrics_analysis": metrics_analysis,
            "recommendations": recommendations,
        }

        # If LLM client is available, get AI-powered insights
        if self._llm_client and target_role:
            try:
                ai_insights = await self._get_ai_insights(
                    resume_text, target_role, job_description
                )
                result["ai_insights"] = ai_insights
            except Exception as e:
                result["ai_insights_error"] = str(e)

        return result

    def _calculate_role_scores(
        self,
        text: str,
        extracted: Dict[str, Any],
        role_config: Optional[RoleConfig],
    ) -> Dict[str, float]:
        """Calculate scores based on role-specific criteria."""
        scores = {}

        # Keyword match score
        if role_config:
            keywords = role_config.keywords
            matched = sum(1 for kw in keywords if kw in text)
            scores["keyword_match"] = min((matched / len(keywords)) * 100, 100) if keywords else 50
        else:
            scores["keyword_match"] = 50

        # Metrics presence score
        metrics_score = self._score_metrics_presence(text, extracted, role_config)
        scores["metrics_presence"] = metrics_score

        # Experience fit score
        years = extracted.get("years_of_experience", 0) or 0
        if role_config:
            min_years, max_years = role_config.experience_range
            if min_years <= years <= max_years:
                scores["experience_fit"] = 100
            elif years < min_years:
                scores["experience_fit"] = max((years / min_years) * 70, 20) if min_years > 0 else 70
            else:  # years > max_years (overqualified)
                scores["experience_fit"] = 80
        else:
            scores["experience_fit"] = 70

        # Skills/tools score
        skills = extracted.get("skills", [])
        if role_config:
            tools_in_resume = sum(1 for kw in role_config.keywords if any(kw in s.lower() for s in skills))
            scores["tools_skills"] = min(tools_in_resume * 15, 100)
        else:
            scores["tools_skills"] = min(len(skills) * 10, 100)

        # Quantification score (has numbers/percentages)
        import re
        metrics_found = len(re.findall(r'\d+%|\$[\d,]+|\d+\+?(?:\s*deals?|\s*meetings?|\s*calls?)', text))
        scores["quantification"] = min(metrics_found * 10, 100)

        # Calculate weighted overall
        if role_config:
            # Use role-specific weights
            overall = (
                scores["keyword_match"] * 0.25 +
                scores["metrics_presence"] * 0.25 +
                scores["experience_fit"] * 0.20 +
                scores["tools_skills"] * 0.15 +
                scores["quantification"] * 0.15
            )
        else:
            overall = sum(scores.values()) / len(scores)

        scores["overall"] = round(overall, 2)
        return scores

    def _score_metrics_presence(
        self,
        text: str,
        extracted: Dict[str, Any],
        role_config: Optional[RoleConfig],
    ) -> float:
        """Score the presence of relevant sales metrics."""
        if not role_config:
            return 50

        metrics_keywords = role_config.metrics_keywords
        found = sum(1 for kw in metrics_keywords if kw in text)

        if not metrics_keywords:
            return 50

        return min((found / len(metrics_keywords)) * 100, 100)

    def _analyze_keywords(
        self,
        text: str,
        role_config: Optional[RoleConfig],
    ) -> Dict[str, Any]:
        """Analyze keyword presence and gaps."""
        if not role_config:
            return {"matched": [], "missing": [], "match_percentage": 0}

        keywords = role_config.keywords
        matched = [kw for kw in keywords if kw in text]
        missing = [kw for kw in keywords if kw not in text]

        return {
            "matched": matched,
            "missing": missing[:10],  # Top 10 missing
            "match_percentage": round((len(matched) / len(keywords)) * 100, 1) if keywords else 0,
        }

    def _analyze_metrics(
        self,
        text: str,
        extracted: Dict[str, Any],
        role_config: Optional[RoleConfig],
    ) -> Dict[str, Any]:
        """Analyze sales metrics presence."""
        import re

        # Find quantified achievements
        patterns = {
            "percentages": r'\d+%',
            "dollar_amounts": r'\$[\d,]+[KMB]?',
            "quota_mentions": r'(?:quota|target).*?\d+',
            "deal_counts": r'\d+\+?\s*deals?',
            "meeting_counts": r'\d+\+?\s*meetings?',
        }

        found_metrics = {}
        for metric_type, pattern in patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                found_metrics[metric_type] = matches[:5]  # Keep top 5

        # Check role-specific metrics
        missing_metrics = []
        if role_config:
            for metric_kw in role_config.metrics_keywords:
                if metric_kw not in text:
                    missing_metrics.append(metric_kw)

        return {
            "found_metrics": found_metrics,
            "missing_metric_types": missing_metrics[:5],
            "metrics_score": len(found_metrics) * 20,  # Max 100 for 5+ types
        }

    def _generate_recommendations(
        self,
        scores: Dict[str, float],
        keyword_analysis: Dict[str, Any],
        metrics_analysis: Dict[str, Any],
        role_config: Optional[RoleConfig],
    ) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []

        # Keyword recommendations
        if keyword_analysis.get("match_percentage", 0) < 50:
            missing = keyword_analysis.get("missing", [])[:3]
            if missing:
                recommendations.append(
                    f"Add relevant keywords: {', '.join(missing)}"
                )

        # Metrics recommendations
        if scores.get("quantification", 0) < 50:
            recommendations.append(
                "Add more quantified achievements (percentages, dollar amounts, deal counts)"
            )

        missing_metrics = metrics_analysis.get("missing_metric_types", [])
        if missing_metrics:
            recommendations.append(
                f"Include metrics for: {', '.join(missing_metrics[:3])}"
            )

        # Experience fit recommendations
        if scores.get("experience_fit", 0) < 70:
            if role_config:
                min_y, max_y = role_config.experience_range
                recommendations.append(
                    f"This role typically requires {min_y}-{max_y} years of experience"
                )

        # Tools/skills recommendations
        if scores.get("tools_skills", 0) < 50:
            recommendations.append(
                "Highlight relevant sales tools and methodologies (Salesforce, Outreach, MEDDIC, etc.)"
            )

        # General recommendations
        if scores.get("overall", 0) >= 80:
            recommendations.insert(0, "Strong resume for this role! Consider these refinements:")
        elif scores.get("overall", 0) >= 60:
            recommendations.insert(0, "Good foundation. Key improvements needed:")
        else:
            recommendations.insert(0, "Significant improvements needed for this role:")

        return recommendations

    async def _get_ai_insights(
        self,
        resume_text: str,
        target_role: str,
        job_description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get AI-powered insights using the LLM client.

        This is a placeholder that will be implemented when LLM integration is added.
        """
        if not self._llm_client:
            return {"error": "LLM client not configured"}

        system_prompt = self.get_system_prompt(
            role=target_role,
            include_jd_matching=job_description is not None,
        )

        user_message = f"""Please analyze this resume for a {ROLE_DISPLAY_NAMES.get(target_role, target_role)} role:

RESUME:
{resume_text}
"""

        if job_description:
            user_message += f"""
JOB DESCRIPTION:
{job_description}
"""

        try:
            response = await self._llm_client(system_prompt, user_message)
            return {"insights": response}
        except Exception as e:
            return {"error": str(e)}


# Singleton instance
_resume_agent: Optional[ResumeAgent] = None


def get_agent() -> ResumeAgent:
    """Get the resume agent singleton."""
    global _resume_agent
    if _resume_agent is None:
        _resume_agent = ResumeAgent()
    return _resume_agent


async def analyze_resume(
    resume_text: str,
    target_role: Optional[str] = None,
    extracted_data: Optional[Dict[str, Any]] = None,
    job_description: Optional[str] = None,
) -> Dict[str, Any]:
    """Convenience function to analyze a resume."""
    agent = get_agent()
    return await agent.analyze_resume(
        resume_text, target_role, extracted_data, job_description
    )


def get_system_prompt(
    role: Optional[str] = None,
    include_jd_matching: bool = False,
) -> str:
    """Convenience function to get the system prompt."""
    agent = get_agent()
    return agent.get_system_prompt(role, include_jd_matching)


def get_role_keywords(role: str) -> List[str]:
    """Convenience function to get role-specific keywords."""
    agent = get_agent()
    return agent.get_role_keywords(role)
