"""
Metrics Extractor service for identifying and collecting sales metrics from resumes.
"""

import os
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum


class MetricType(str, Enum):
    """Types of sales metrics."""
    QUOTA_ATTAINMENT = "quota_attainment"
    REVENUE_CLOSED = "revenue_closed"
    DEALS_CLOSED = "deals_closed"
    AVERAGE_DEAL_SIZE = "average_deal_size"
    WIN_RATE = "win_rate"
    MEETINGS_BOOKED = "meetings_booked"
    SQLS_GENERATED = "sqls_generated"
    ACTIVITY_METRICS = "activity_metrics"
    NRR = "net_revenue_retention"
    CHURN_RATE = "churn_rate"
    EXPANSION_REVENUE = "expansion_revenue"
    TEAM_SIZE = "team_size"
    TEAM_QUOTA = "team_quota"


@dataclass
class ExtractedMetric:
    """A metric extracted from resume text."""
    metric_type: str
    value: str
    context: str  # Surrounding text for reference
    confidence: float = 1.0


@dataclass
class MissingMetric:
    """A metric that should be present but is missing."""
    metric_type: str
    question: str
    company: str
    role: str
    priority: int = 1  # 1 = highest priority


@dataclass
class MetricsExtractionResult:
    """Result of metrics extraction analysis."""
    metrics_found: List[ExtractedMetric] = field(default_factory=list)
    metrics_missing: List[MissingMetric] = field(default_factory=list)
    overall_score: int = 0  # 0-100 score of how well metrics are quantified
    recommendations: List[str] = field(default_factory=list)


# Role-specific metric requirements
ROLE_METRICS = {
    "entry_sdr": {
        "required": ["quota_attainment", "meetings_booked", "activity_metrics"],
        "optional": ["sqls_generated", "ramp_time"],
    },
    "sdr": {
        "required": ["quota_attainment", "meetings_booked", "sqls_generated", "activity_metrics"],
        "optional": ["team_ranking", "ramp_time"],
    },
    "account_executive": {
        "required": ["quota_attainment", "revenue_closed", "deals_closed", "average_deal_size"],
        "optional": ["win_rate", "sales_cycle", "self_sourced_pipeline"],
    },
    "senior_ae": {
        "required": ["quota_attainment", "revenue_closed", "deals_closed", "average_deal_size", "largest_deal"],
        "optional": ["win_rate", "named_logos", "multi_stakeholder", "land_expand"],
    },
    "account_manager": {
        "required": ["net_revenue_retention", "expansion_revenue", "book_of_business"],
        "optional": ["churn_rate", "logo_retention", "upsell_rate"],
    },
    "sales_manager": {
        "required": ["team_quota_attainment", "team_size", "revenue_responsibility"],
        "optional": ["rep_development", "hiring_track_record", "promotions"],
    },
}

# Patterns for extracting metrics from resume text
METRIC_PATTERNS = {
    "quota_attainment": [
        r"(\d{2,3})%\s*(?:of\s+)?quota",
        r"quota\s*(?:attainment|achievement)[:\s]+(\d{2,3})%",
        r"achieved\s+(\d{2,3})%\s*(?:of\s+)?(?:sales\s+)?(?:quota|target)",
        r"(\d{2,3})%\s*quota\s+attainment",
    ],
    "revenue_closed": [
        r"\$(\d+(?:\.\d+)?[MKB]?)\s*(?:in\s+)?(?:closed|revenue|ARR|ACV)",
        r"closed\s+\$(\d+(?:\.\d+)?[MKB]?)",
        r"(?:generated|drove|closed)\s+\$(\d+(?:\.\d+)?[MKB]?)\s*(?:in\s+)?(?:revenue|ARR|pipeline)",
    ],
    "deals_closed": [
        r"closed\s+(\d+)\s*(?:\+\s*)?deals",
        r"(\d+)\s*deals?\s*closed",
        r"won\s+(\d+)\s*(?:\+\s*)?(?:deals|accounts|opportunities)",
    ],
    "average_deal_size": [
        r"(?:average|avg)\s*(?:deal\s*)?(?:size|ACV)[:\s]+\$(\d+(?:\.\d+)?[MK]?)",
        r"\$(\d+(?:\.\d+)?[MK]?)\s*(?:average|avg)\s*(?:deal\s*)?(?:size|ACV)",
    ],
    "win_rate": [
        r"(\d{1,2})%\s*win\s*rate",
        r"win\s*rate[:\s]+(\d{1,2})%",
    ],
    "meetings_booked": [
        r"(\d+)\s*(?:\+\s*)?(?:meetings?|demos?)\s*(?:booked|scheduled)",
        r"booked\s+(\d+)\s*(?:\+\s*)?(?:meetings?|demos?)",
        r"(\d+)\s*(?:meetings?|demos?)/(?:month|week|quarter)",
    ],
    "sqls_generated": [
        r"(\d+)\s*(?:\+\s*)?SQLs?",
        r"generated\s+(\d+)\s*(?:\+\s*)?(?:qualified\s+)?leads?",
    ],
    "activity_metrics": [
        r"(\d+)\s*(?:\+\s*)?(?:calls?|dials?)/(?:day|week)",
        r"(\d+)\s*(?:\+\s*)?emails?/(?:day|week)",
    ],
    "net_revenue_retention": [
        r"(\d{2,3})%\s*(?:net\s+)?(?:revenue\s+)?retention",
        r"NRR[:\s]+(\d{2,3})%",
    ],
    "team_size": [
        r"(?:managed|led|oversaw)\s*(?:a\s+)?(?:team\s+of\s+)?(\d+)\s*(?:\+\s*)?(?:reps?|SDRs?|AEs?|people)",
        r"(\d+)\s*(?:\+\s*)?(?:direct\s+)?reports?",
    ],
    "team_quota": [
        r"team\s*(?:quota\s*)?(?:attainment|achievement)[:\s]+(\d{2,3})%",
        r"(\d{2,3})%\s*team\s*(?:quota|target)",
    ],
}

# Question templates for missing metrics
QUESTION_TEMPLATES = {
    "quota_attainment": "What was your quota attainment percentage at {company} as {role}?",
    "revenue_closed": "How much total revenue did you close at {company}? (e.g., $500K, $2M)",
    "deals_closed": "How many deals did you close at {company}?",
    "average_deal_size": "What was your average deal size (ACV) at {company}?",
    "win_rate": "What was your win rate at {company}?",
    "meetings_booked": "How many meetings/demos did you book per month at {company}?",
    "sqls_generated": "How many SQLs did you generate at {company}?",
    "activity_metrics": "What were your daily/weekly activity numbers (calls, emails) at {company}?",
    "net_revenue_retention": "What was the Net Revenue Retention (NRR) for your book of business at {company}?",
    "expansion_revenue": "How much expansion revenue did you generate at {company}?",
    "churn_rate": "What was the churn rate for your accounts at {company}?",
    "book_of_business": "What was the total value of your book of business at {company}?",
    "team_size": "How many people were on the team you managed at {company}?",
    "team_quota_attainment": "What was your team's quota attainment at {company}?",
    "revenue_responsibility": "What was the total revenue your team was responsible for at {company}?",
    "largest_deal": "What was the largest deal you closed at {company}?",
    "named_logos": "What notable/enterprise logos did you close at {company}?",
}


class MetricsExtractor:
    """Service for extracting and analyzing sales metrics from resumes."""

    def __init__(self):
        self._llm_available = bool(os.getenv("ANTHROPIC_API_KEY"))

    def is_available(self) -> bool:
        """Check if the service is available."""
        return True  # Rule-based extraction is always available

    def extract_metrics(
        self,
        resume_text: str,
        target_role: str,
        extracted_data: Optional[Dict[str, Any]] = None,
    ) -> MetricsExtractionResult:
        """
        Extract metrics from resume text and identify what's missing.

        Args:
            resume_text: The full resume text
            target_role: Target sales role (sdr, account_executive, etc.)
            extracted_data: Optional pre-extracted resume data

        Returns:
            MetricsExtractionResult with found and missing metrics
        """
        result = MetricsExtractionResult()

        # Get role-specific requirements
        role_config = ROLE_METRICS.get(target_role, ROLE_METRICS["account_executive"])
        required_metrics = role_config.get("required", [])
        optional_metrics = role_config.get("optional", [])

        # Extract metrics using patterns
        found_metric_types = set()
        for metric_type, patterns in METRIC_PATTERNS.items():
            for pattern in patterns:
                matches = re.finditer(pattern, resume_text, re.IGNORECASE)
                for match in matches:
                    value = match.group(1)
                    context = resume_text[max(0, match.start() - 50):min(len(resume_text), match.end() + 50)]
                    result.metrics_found.append(ExtractedMetric(
                        metric_type=metric_type,
                        value=value,
                        context=context.strip(),
                    ))
                    found_metric_types.add(metric_type)

        # Extract company names from resume for context
        companies = self._extract_companies(resume_text, extracted_data)

        # Identify missing metrics
        priority = 1
        for metric_type in required_metrics:
            if metric_type not in found_metric_types:
                question_template = QUESTION_TEMPLATES.get(metric_type, f"Can you provide your {metric_type.replace('_', ' ')}?")
                for company, role in companies[:3]:  # Limit to recent 3 companies
                    result.metrics_missing.append(MissingMetric(
                        metric_type=metric_type,
                        question=question_template.format(company=company, role=role),
                        company=company,
                        role=role,
                        priority=priority,
                    ))
                priority += 1

        # Calculate overall score
        total_relevant = len(required_metrics) + len(optional_metrics)
        found_required = len(found_metric_types.intersection(required_metrics))
        found_optional = len(found_metric_types.intersection(optional_metrics))

        if total_relevant > 0:
            # Required metrics weighted 2x
            weighted_score = (found_required * 2 + found_optional) / (len(required_metrics) * 2 + len(optional_metrics))
            result.overall_score = int(weighted_score * 100)

        # Generate recommendations
        if result.overall_score < 50:
            result.recommendations.append(
                "Your resume is missing critical sales metrics. Adding quantified achievements can increase interview rates by 40%."
            )
        if "quota_attainment" not in found_metric_types and "quota_attainment" in required_metrics:
            result.recommendations.append(
                "Quota attainment is the #1 metric recruiters look for. Add it to every sales role on your resume."
            )
        if len(found_metric_types) < 3:
            result.recommendations.append(
                "Aim to include at least 3-5 quantified metrics per role to demonstrate impact."
            )

        return result

    def _extract_companies(
        self,
        resume_text: str,
        extracted_data: Optional[Dict[str, Any]] = None,
    ) -> List[tuple]:
        """Extract company names and roles from resume."""
        companies = []

        # Try to get from extracted data first
        if extracted_data:
            experience = extracted_data.get("experience", [])
            for exp in experience:
                company = exp.get("company", "your company")
                title = exp.get("title", "your role")
                companies.append((company, title))

        # Fallback: try to extract from text
        if not companies:
            # Common patterns for company/role
            patterns = [
                r"(?:at|with)\s+([A-Z][A-Za-z0-9\s&]+(?:Inc|LLC|Corp|Company)?)",
                r"([A-Z][A-Za-z0-9\s&]+)\s*[-|]\s*(?:SDR|BDR|AE|Account Executive|Sales)",
            ]
            for pattern in patterns:
                matches = re.findall(pattern, resume_text)
                for match in matches[:3]:
                    companies.append((match.strip(), "your role"))

        # Default if nothing found
        if not companies:
            companies = [("your most recent company", "your role")]

        return companies

    def format_metrics_for_resume(
        self,
        metrics: Dict[str, Dict[str, str]],
        target_role: str,
    ) -> Dict[str, str]:
        """
        Format collected metrics into resume-ready bullet points.

        Args:
            metrics: Dict of {company: {metric_type: value}}
            target_role: Target sales role

        Returns:
            Dict of {company: formatted_bullet_points}
        """
        formatted = {}

        for company, company_metrics in metrics.items():
            bullets = []

            # Format based on metric type
            if "quota_attainment" in company_metrics:
                value = company_metrics["quota_attainment"]
                bullets.append(f"Achieved {value}% of quota consistently")

            if "revenue_closed" in company_metrics:
                value = company_metrics["revenue_closed"]
                bullets.append(f"Closed ${value} in new business revenue")

            if "deals_closed" in company_metrics:
                value = company_metrics["deals_closed"]
                if "average_deal_size" in company_metrics:
                    acv = company_metrics["average_deal_size"]
                    bullets.append(f"Won {value} deals with ${acv} average ACV")
                else:
                    bullets.append(f"Successfully closed {value} deals")

            if "meetings_booked" in company_metrics:
                value = company_metrics["meetings_booked"]
                bullets.append(f"Booked {value}+ qualified meetings per month")

            if "sqls_generated" in company_metrics:
                value = company_metrics["sqls_generated"]
                bullets.append(f"Generated {value}+ SQLs through outbound prospecting")

            if "win_rate" in company_metrics:
                value = company_metrics["win_rate"]
                bullets.append(f"Maintained {value}% win rate")

            if "net_revenue_retention" in company_metrics:
                value = company_metrics["net_revenue_retention"]
                bullets.append(f"Drove {value}% Net Revenue Retention")

            if "team_size" in company_metrics:
                value = company_metrics["team_size"]
                bullets.append(f"Led team of {value} sales professionals")

            formatted[company] = "\n".join(f"• {b}" for b in bullets)

        return formatted


# Singleton instance
_extractor: Optional[MetricsExtractor] = None


def get_extractor() -> MetricsExtractor:
    """Get singleton MetricsExtractor instance."""
    global _extractor
    if _extractor is None:
        _extractor = MetricsExtractor()
    return _extractor
