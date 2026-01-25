"""
Quick Scoring Service for Polished Resume Ranking System.
Implements rule-based scoring for the free tier.
Enhanced for tech sales with research-backed scoring criteria.
"""

from typing import Dict, List, Optional, Any, Tuple
import re
import math
from dataclasses import dataclass
from enum import Enum


class ScoreCategory(str, Enum):
    """Scoring categories."""
    EXPERIENCE = "experience"
    SKILLS = "skills"
    EDUCATION = "education"
    FORMATTING = "formatting"
    KEYWORDS = "keywords"
    CONTACT_INFO = "contact_info"
    # New tech sales categories
    ACHIEVEMENTS = "achievements"
    CERTIFICATIONS = "certifications"
    CAREER_PROGRESSION = "career_progression"


@dataclass
class ScoringWeights:
    """Configurable scoring weights (generic/legacy)."""
    experience: float = 0.25
    skills: float = 0.30
    education: float = 0.15
    formatting: float = 0.10
    keywords: float = 0.15
    contact_info: float = 0.05

    def __post_init__(self):
        """Validate that weights sum to 1.0."""
        total = sum(self.to_dict().values())
        if not (0.99 <= total <= 1.01):  # Allow small floating point variance
            raise ValueError(f"Weights must sum to 1.0, got {total}")

    def to_dict(self) -> Dict[str, float]:
        return {
            "experience": self.experience,
            "skills": self.skills,
            "education": self.education,
            "formatting": self.formatting,
            "keywords": self.keywords,
            "contact_info": self.contact_info,
        }


@dataclass
class TechSalesScoringWeights:
    """
    Tech sales-specific scoring weights based on 2025-2026 recruiter priorities.
    Research sources: Resume Worded, Enhancv, Highspot, Everstage
    """
    experience: float = 0.20
    skills: float = 0.20
    education: float = 0.05  # Less important for sales roles
    formatting: float = 0.08
    keywords: float = 0.10
    contact_info: float = 0.02
    # New categories - critical for tech sales
    achievements: float = 0.18  # #1 differentiator per recruiters
    certifications: float = 0.08
    career_progression: float = 0.09

    def __post_init__(self):
        """Validate that weights sum to 1.0."""
        total = sum(self.to_dict().values())
        if not (0.99 <= total <= 1.01):  # Allow small floating point variance
            raise ValueError(f"Weights must sum to 1.0, got {total}")

    def to_dict(self) -> Dict[str, float]:
        return {
            "experience": self.experience,
            "skills": self.skills,
            "education": self.education,
            "formatting": self.formatting,
            "keywords": self.keywords,
            "contact_info": self.contact_info,
            "achievements": self.achievements,
            "certifications": self.certifications,
            "career_progression": self.career_progression,
        }


# Default technical skills by category
SKILL_CATEGORIES = {
    "programming_languages": [
        "python", "javascript", "typescript", "java", "c++", "c#", "go", "rust",
        "ruby", "php", "swift", "kotlin", "scala", "r", "matlab", "perl",
    ],
    "frontend": [
        "react", "angular", "vue", "svelte", "next.js", "nuxt", "gatsby",
        "html", "css", "sass", "less", "tailwind", "bootstrap", "material-ui",
    ],
    "backend": [
        "node.js", "express", "fastapi", "django", "flask", "spring", "rails",
        "asp.net", "laravel", "gin", "echo", "fiber",
    ],
    "databases": [
        "sql", "postgresql", "mysql", "mongodb", "redis", "elasticsearch",
        "dynamodb", "cassandra", "oracle", "sqlite", "neo4j",
    ],
    "cloud": [
        "aws", "azure", "gcp", "google cloud", "heroku", "digitalocean",
        "lambda", "ec2", "s3", "cloudfront", "route53",
    ],
    "devops": [
        "docker", "kubernetes", "terraform", "ansible", "jenkins", "gitlab",
        "github actions", "circleci", "travis", "prometheus", "grafana",
    ],
    "data_science": [
        "machine learning", "deep learning", "tensorflow", "pytorch", "keras",
        "scikit-learn", "pandas", "numpy", "nlp", "computer vision",
    ],
    "soft_skills": [
        "leadership", "communication", "teamwork", "problem-solving",
        "agile", "scrum", "mentoring", "project management",
    ],
}

# Flattened skill list
ALL_SKILLS = []
for category, skills in SKILL_CATEGORIES.items():
    ALL_SKILLS.extend(skills)

# Education levels and their scores
EDUCATION_LEVELS = {
    "phd": 100,
    "doctorate": 100,
    "ph.d": 100,
    "master": 85,
    "mba": 85,
    "m.s.": 85,
    "m.s": 85,
    "ms": 80,
    "bachelor": 70,
    "b.s.": 70,
    "b.s": 70,
    "bs": 65,
    "associate": 50,
    "bootcamp": 40,
    "certificate": 35,
    "certification": 35,
    "diploma": 30,
}

# Common action verbs that indicate strong resume writing
ACTION_VERBS = [
    "achieved", "accomplished", "accelerated", "administered", "analyzed",
    "built", "collaborated", "created", "delivered", "designed", "developed",
    "drove", "engineered", "established", "executed", "expanded", "grew",
    "implemented", "improved", "increased", "initiated", "innovated", "launched",
    "led", "managed", "mentored", "optimized", "orchestrated", "pioneered",
    "reduced", "redesigned", "refactored", "scaled", "spearheaded", "streamlined",
    "transformed", "upgraded",
]

# ============================================================================
# TECH SALES SCORING CONSTANTS (2025-2026)
# Based on research from Resume Worded, Enhancv, Highspot, Everstage
# ============================================================================

# Achievement patterns - critical for tech sales (avg quota attainment is 43-65%)
ACHIEVEMENT_PATTERNS = {
    "quota": [
        r"(\d+)%\s*(?:of\s+)?quota",
        r"(?:achieved|exceeded|attained)\s*(\d+)%",
        r"quota\s*(?:attainment|achievement)[:\s]*(\d+)%",
        r"(\d+)%\s*(?:to|of)\s*(?:target|goal|plan)",
    ],
    "revenue": [
        r"\$[\d,]+(?:\s*[KMB])?\s*(?:arr|mrr|revenue|pipeline|closed)",
        r"(\d+(?:\.\d+)?)\s*(?:million|M)\s*(?:in\s+)?(?:revenue|arr|pipeline)",
        r"(?:generated|closed|contributed)\s*\$[\d,]+[KMB]?",
    ],
    "deals": [
        r"(\d+)\+?\s*(?:deals?|opportunities|accounts?)\s*(?:closed|won)?",
        r"(?:closed|won)\s*(\d+)\+?\s*(?:deals?|opportunities)",
        r"average\s*(?:deal|contract)\s*(?:size|value)[:\s]*\$[\d,]+[KMB]?",
        r"acv[:\s]*\$[\d,]+[KMB]?",
    ],
    "ranking": [
        r"(?:top|#)(\d+)\s*(?:of|out of|/)\s*(\d+)",
        r"president'?s?\s*club",
        r"top\s*(\d+)%\s*(?:performer|rep|sales)?",
        r"(?:sales|quota)\s*(?:champion|winner|leader)",
        r"(?:rookie|rep)\s*of\s*(?:the\s+)?(?:year|quarter|month)",
    ],
    "activity": [
        r"(\d+)\+?\s*(?:calls?|dials?)\s*(?:per|daily|/)\s*(?:day|week)?",
        r"(\d+)\+?\s*(?:meetings?|demos?)\s*(?:booked|scheduled|set)",
        r"(\d+)\+?\s*(?:sqls?|mqls?|leads?)\s*(?:generated|qualified)",
        r"(\d+)%\s*(?:conversion|response)\s*rate",
    ],
    "growth": [
        r"(\d+)%\s*(?:yoy|year-over-year|growth)",
        r"(?:grew|expanded|increased)\s*(?:by\s+)?(\d+)%",
        r"(?:nrr|net revenue retention)[:\s]*(\d+)%",
        r"(?:reduced|decreased)\s*churn\s*(?:by\s+)?(\d+)%",
    ],
}

# Sales certifications by value tier
SALES_CERTIFICATIONS = {
    "high_value": [
        "salesforce certified", "salesforce administrator", "salesforce sales cloud",
        "hubspot certified", "hubspot sales", "hubspot inbound sales",
        "meddic certified", "meddpicc",
        "sandler certified", "challenger certified",
    ],
    "medium_value": [
        "gong certified", "outreach certified",
        "linkedin sales navigator", "zoominfo certified",
        "spin selling", "solution selling certified",
        "value selling", "consultative selling",
    ],
    "bonus": [
        "aws certified", "google ads certified", "google analytics",
        "product certified", "scrum certified", "pmp",
        "csm", "customer success",
    ],
}

# Sales title progression levels for career trajectory scoring
SALES_TITLE_LEVELS = {
    1: ["intern", "trainee", "associate", "entry"],
    2: ["sdr", "bdr", "sales development", "business development rep", "lead generation"],
    3: ["account executive", "ae", "inside sales", "field sales", "sales rep"],
    4: ["senior", "enterprise", "strategic", "principal", "major accounts"],
    5: ["manager", "director", "vp", "head of", "chief revenue", "cro"],
}

# Tech sales skills by category (2025-2026 stack)
TECH_SALES_SKILLS = {
    "crm": [
        "salesforce", "hubspot", "dynamics 365", "microsoft dynamics",
        "zoho crm", "pipedrive", "freshsales", "close.io",
    ],
    "engagement": [
        "outreach", "salesloft", "apollo", "groove", "mixmax",
        "yesware", "reply.io", "lemlist", "mailshake",
    ],
    "intelligence": [
        "gong", "chorus", "clari", "revenue.io", "wingman",
        "jiminny", "refract", "execvision", "conversation intelligence",
    ],
    "prospecting": [
        "linkedin sales navigator", "zoominfo", "apollo",
        "lusha", "seamless.ai", "clearbit", "6sense",
        "demandbase", "clay", "cognism",
    ],
    "methodologies": [
        "meddic", "meddpicc", "bant", "challenger", "spin",
        "sandler", "solution selling", "value selling",
        "gap selling", "consultative selling", "command of message",
    ],
    "core_skills": [
        "cold calling", "prospecting", "discovery", "demo",
        "negotiation", "closing", "forecasting", "pipeline management",
        "territory planning", "account mapping", "objection handling",
        "contract negotiation", "multi-threading", "stakeholder management",
    ],
    "soft_skills": [
        "presentation", "communication", "relationship building",
        "consultative", "strategic", "cross-functional", "collaborative",
        "coachable", "resilient", "self-motivated", "competitive",
    ],
    # AI/Automation skills (emerging 2025-2026)
    "ai_automation": [
        "chatgpt", "claude", "ai assistant", "ai tools", "generative ai",
        "sales automation", "workflow automation", "zapier", "make.com",
        "ai prospecting", "ai-powered", "machine learning",
        "predictive analytics", "sales intelligence", "intent data",
    ],
}

# Flatten tech sales skills for quick lookup
ALL_TECH_SALES_SKILLS = []
for category, skills in TECH_SALES_SKILLS.items():
    ALL_TECH_SALES_SKILLS.extend(skills)


def _progressive_score(value: float, optimal: float, max_points: float) -> float:
    """
    Calculate score with smooth curve instead of hard thresholds.
    Uses exponential approach for diminishing returns.

    Args:
        value: The actual value (e.g., years of experience)
        optimal: The optimal value where max score is achieved
        max_points: Maximum points for this metric

    Returns:
        Score from 0 to max_points with smooth progression
    """
    if value <= 0:
        return 0.0
    if value >= optimal:
        return max_points
    ratio = value / optimal
    # Exponential curve: fast gains early, slower later
    return max_points * (1 - math.exp(-3 * ratio))


class QuickScorer:
    """
    Rule-based resume scoring service.
    Provides fast, deterministic scoring without LLM calls.
    Supports both generic and tech sales-specific scoring.
    """

    def __init__(
        self,
        weights: Optional[ScoringWeights] = None,
        use_tech_sales: bool = False
    ):
        """
        Initialize the scorer.

        Args:
            weights: Custom scoring weights (optional)
            use_tech_sales: If True, use TechSalesScoringWeights by default
        """
        if weights:
            self.weights = weights
        elif use_tech_sales:
            self.weights = TechSalesScoringWeights()
        else:
            self.weights = ScoringWeights()
        self.is_tech_sales = use_tech_sales or isinstance(self.weights, TechSalesScoringWeights)

    async def score_resume(
        self,
        text: str,
        extracted_data: Optional[Dict[str, Any]] = None,
        job_keywords: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Score a resume based on multiple criteria.

        Args:
            text: Raw resume text
            extracted_data: Pre-extracted structured data
            job_keywords: Optional keywords to match against

        Returns:
            Dictionary with category scores and overall score
        """
        text_lower = text.lower()
        extracted = extracted_data or {}

        # Calculate base category scores
        scores = {
            ScoreCategory.EXPERIENCE.value: self._score_experience(text_lower, extracted),
            ScoreCategory.SKILLS.value: self._score_skills(text_lower, extracted),
            ScoreCategory.EDUCATION.value: self._score_education(text_lower, extracted),
            ScoreCategory.FORMATTING.value: self._score_formatting(text),
            ScoreCategory.KEYWORDS.value: self._score_keywords(text_lower, job_keywords),
            ScoreCategory.CONTACT_INFO.value: self._score_contact_info(extracted),
        }

        # Add tech sales-specific scores if using tech sales weights
        if self.is_tech_sales:
            scores[ScoreCategory.ACHIEVEMENTS.value] = self._score_achievements(text_lower, extracted)
            scores[ScoreCategory.CERTIFICATIONS.value] = self._score_certifications(text_lower)
            scores[ScoreCategory.CAREER_PROGRESSION.value] = self._score_career_progression(text_lower, extracted)

        # Calculate weighted overall score
        weights = self.weights.to_dict()
        overall = sum(
            scores[cat] * weights.get(cat, 0)
            for cat in scores
        )

        scores["overall"] = round(overall, 2)

        return scores

    def _score_experience(
        self,
        text: str,
        extracted: Dict[str, Any]
    ) -> float:
        """Score based on work experience using progressive scoring."""
        score = 0

        # Years of experience - use progressive scoring
        years = extracted.get("years_of_experience", 0) or 0

        if self.is_tech_sales:
            # For tech sales: optimal is 5-8 years for AE roles
            score += _progressive_score(years, 7, 40)
        else:
            # Original hard threshold approach (kept for backward compatibility)
            if years >= 10:
                score += 40
            elif years >= 7:
                score += 35
            elif years >= 5:
                score += 30
            elif years >= 3:
                score += 25
            elif years >= 1:
                score += 15
            else:
                score += 5

        # Number of positions/roles
        experience_list = extracted.get("experience", [])
        if isinstance(experience_list, list):
            position_count = len(experience_list)
            score += min(position_count * 5, 20)

        # Action verbs usage
        action_verb_count = sum(1 for verb in ACTION_VERBS if verb in text)
        score += min(action_verb_count * 2, 20)

        # Quantifiable achievements (numbers, percentages)
        metrics = re.findall(r'\d+%|\$\d+|\d+\+', text)
        score += min(len(metrics) * 3, 20)

        return min(score, 100)

    def _score_skills(
        self,
        text: str,
        extracted: Dict[str, Any]
    ) -> float:
        """Score based on technical and soft skills."""
        score = 0
        found_skills = set()

        # Count skills from extracted data
        extracted_skills = extracted.get("skills", [])
        if isinstance(extracted_skills, list):
            found_skills.update(s.lower() for s in extracted_skills)

        # Use appropriate skill list based on scoring mode
        if self.is_tech_sales:
            skill_list = ALL_TECH_SALES_SKILLS
            skill_categories = TECH_SALES_SKILLS
        else:
            skill_list = ALL_SKILLS
            skill_categories = SKILL_CATEGORIES

        # Find skills in text
        for skill in skill_list:
            if skill in text:
                found_skills.add(skill)

        skill_count = len(found_skills)

        if self.is_tech_sales:
            # Tech sales scoring: prioritize tools and methodologies
            crm_found = any(s in found_skills for s in TECH_SALES_SKILLS["crm"])
            engagement_found = any(s in found_skills for s in TECH_SALES_SKILLS["engagement"])
            intelligence_found = any(s in found_skills for s in TECH_SALES_SKILLS["intelligence"])
            prospecting_found = any(s in found_skills for s in TECH_SALES_SKILLS["prospecting"])
            methodology_found = any(s in found_skills for s in TECH_SALES_SKILLS["methodologies"])

            # CRM proficiency is critical
            if crm_found:
                score += 20
            # Engagement tools
            if engagement_found:
                score += 15
            # Intelligence tools (Gong, Chorus)
            if intelligence_found:
                score += 15
            # Prospecting tools
            if prospecting_found:
                score += 10
            # Methodology knowledge (MEDDIC, Challenger, etc.)
            if methodology_found:
                score += 20

            # Soft skills diversity
            soft_skills_found = sum(1 for s in TECH_SALES_SKILLS["soft_skills"] if s in found_skills)
            score += min(soft_skills_found * 3, 10)

            # Core sales skills
            core_skills_found = sum(1 for s in TECH_SALES_SKILLS["core_skills"] if s in found_skills)
            score += min(core_skills_found * 2, 10)

            # AI/Automation bonus (emerging 2025-2026)
            ai_skills_found = any(s in text for s in TECH_SALES_SKILLS["ai_automation"])
            if ai_skills_found:
                score += 10
        else:
            # Original generic scoring
            # Score based on skill count
            if skill_count >= 15:
                score += 50
            elif skill_count >= 10:
                score += 40
            elif skill_count >= 7:
                score += 30
            elif skill_count >= 4:
                score += 20
            elif skill_count >= 1:
                score += 10

            # Bonus for skill diversity (different categories)
            categories_covered = set()
            for category, skills in skill_categories.items():
                if any(s in found_skills for s in skills):
                    categories_covered.add(category)

            score += min(len(categories_covered) * 7, 35)

            # Check for advanced/senior indicators
            seniority_keywords = ["senior", "lead", "principal", "staff", "architect", "expert"]
            if any(kw in text for kw in seniority_keywords):
                score += 15

        return min(score, 100)

    def _score_education(
        self,
        text: str,
        extracted: Dict[str, Any]
    ) -> float:
        """Score based on education."""
        score = 0
        highest_level = 0

        # Check for education levels
        for level, level_score in EDUCATION_LEVELS.items():
            if level in text:
                highest_level = max(highest_level, level_score)

        score += highest_level * 0.6

        # Check for relevant fields
        relevant_fields = [
            "computer science", "software engineering", "information technology",
            "electrical engineering", "mathematics", "physics", "data science",
            "machine learning", "artificial intelligence",
        ]

        if any(field in text for field in relevant_fields):
            score += 20

        # Check for prestigious universities (simplified)
        prestigious = [
            "stanford", "mit", "harvard", "berkeley", "carnegie mellon",
            "princeton", "yale", "columbia", "oxford", "cambridge",
        ]

        if any(uni in text for uni in prestigious):
            score += 15

        # Certifications
        certifications = extracted.get("certifications", [])
        if certifications:
            score += min(len(certifications) * 5, 15)

        return min(score, 100)

    def _score_formatting(self, text: str) -> float:
        """Score based on resume structure and formatting."""
        score = 50  # Base score

        # Check length (not too short, not too long)
        word_count = len(text.split())
        if 300 <= word_count <= 800:
            score += 20
        elif 200 <= word_count <= 1000:
            score += 10
        elif word_count < 100 or word_count > 1500:
            score -= 10

        # Check for section headers
        section_headers = [
            "experience", "education", "skills", "projects", "summary",
            "objective", "work history", "employment", "technical skills",
        ]
        headers_found = sum(1 for h in section_headers if h in text.lower())
        score += min(headers_found * 5, 20)

        # Check for bullet points or structured lists
        bullet_patterns = [r'•', r'◦', r'▪', r'\n-\s', r'\n\*\s']
        for pattern in bullet_patterns:
            if re.search(pattern, text):
                score += 5
                break

        # Penalize for common issues
        # Too many special characters
        special_char_ratio = len(re.findall(r'[^a-zA-Z0-9\s.,!?\'-]', text)) / max(len(text), 1)
        if special_char_ratio > 0.1:
            score -= 10

        # All caps sections (might indicate parsing issues)
        caps_ratio = len(re.findall(r'[A-Z]{5,}', text)) / max(len(text.split()), 1)
        if caps_ratio > 0.05:
            score -= 5

        return max(min(score, 100), 0)

    def _score_keywords(
        self,
        text: str,
        job_keywords: Optional[List[str]] = None
    ) -> float:
        """Score based on keyword presence."""
        if not job_keywords:
            # Default keywords for general tech roles
            job_keywords = [
                "software", "development", "engineering", "programming",
                "testing", "deployment", "api", "database", "cloud",
                "agile", "team", "project", "solution", "system",
            ]

        # Count keyword matches
        matched = sum(1 for kw in job_keywords if kw.lower() in text)
        match_ratio = matched / len(job_keywords) if job_keywords else 0

        score = match_ratio * 100

        # Bonus for strong keyword density
        if match_ratio >= 0.7:
            score += 10
        elif match_ratio >= 0.5:
            score += 5

        return min(score, 100)

    def _score_contact_info(self, extracted: Dict[str, Any]) -> float:
        """Score based on contact information completeness."""
        score = 0

        if extracted.get("email"):
            score += 40

        if extracted.get("phone"):
            score += 30

        if extracted.get("name"):
            score += 20

        if extracted.get("location"):
            score += 10

        return min(score, 100)

    # ========================================================================
    # TECH SALES-SPECIFIC SCORING METHODS
    # ========================================================================

    def _score_achievements(
        self,
        text: str,
        extracted: Dict[str, Any]
    ) -> float:
        """
        Score based on quantifiable achievements.
        This is the #1 differentiator for tech sales resumes per recruiter research.
        Average quota attainment is 43-65%, so 100%+ is impressive.
        """
        score = 0
        metrics_found = {}

        # Check each achievement category
        for category, patterns in ACHIEVEMENT_PATTERNS.items():
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    if category not in metrics_found:
                        metrics_found[category] = []
                    metrics_found[category].extend(matches)

        # Score by category (based on recruiter priority)
        if metrics_found.get("quota"):
            score += 25
            # Bonus for high quota attainment (100%+)
            for match in metrics_found["quota"]:
                if isinstance(match, tuple):
                    match = next((m for m in match if m), "")
                try:
                    pct = int(re.search(r'\d+', str(match)).group())
                    if pct >= 100:
                        score += 10
                        break
                except (AttributeError, ValueError):
                    pass

        if metrics_found.get("revenue"):
            score += 20

        if metrics_found.get("deals"):
            score += 15

        if metrics_found.get("ranking"):
            score += 20
            # Extra bonus for President's Club
            if any("president" in str(m).lower() for m in metrics_found["ranking"]):
                score += 5

        if metrics_found.get("activity"):
            score += 10

        if metrics_found.get("growth"):
            score += 10

        # Bonus for having multiple metric types (shows comprehensive track record)
        if len(metrics_found) >= 3:
            score += 10

        return min(score, 100)

    def _score_certifications(self, text: str) -> float:
        """
        Score based on sales-relevant certifications.
        Salesforce, HubSpot, MEDDIC certifications are highly valued.
        """
        score = 0

        # Check high-value certifications
        high_value_found = 0
        for cert in SALES_CERTIFICATIONS["high_value"]:
            if cert in text:
                high_value_found += 1
        score += min(high_value_found * 20, 50)

        # Check medium-value certifications
        medium_value_found = 0
        for cert in SALES_CERTIFICATIONS["medium_value"]:
            if cert in text:
                medium_value_found += 1
        score += min(medium_value_found * 12, 30)

        # Check bonus certifications
        bonus_found = 0
        for cert in SALES_CERTIFICATIONS["bonus"]:
            if cert in text:
                bonus_found += 1
        score += min(bonus_found * 5, 15)

        # Base score if "certified" or "certification" mentioned
        if score == 0 and ("certified" in text or "certification" in text):
            score = 20

        return min(score, 100)

    def _score_career_progression(
        self,
        text: str,
        extracted: Dict[str, Any]
    ) -> float:
        """
        Score based on career trajectory.
        SDR → AE → Senior AE progression is valued by recruiters.
        """
        score = 0
        levels_found = set()

        # Detect title levels from text using word boundaries for short terms
        for level, titles in SALES_TITLE_LEVELS.items():
            for title in titles:
                # Use word boundary matching for short terms to avoid false positives
                if len(title) <= 3:
                    # Match as whole word only (e.g., "ae" shouldn't match "aerospace")
                    if re.search(rf'\b{re.escape(title)}\b', text):
                        levels_found.add(level)
                        break
                elif title in text:
                    levels_found.add(level)
                    break

        # Score based on progression
        if levels_found:
            # Highest level reached
            max_level = max(levels_found)
            score += max_level * 15  # Up to 75 for level 5 (VP/Director)

            # Bonus for showing progression (multiple levels)
            if len(levels_found) >= 2:
                score += 15  # Shows growth

            # Extra bonus for rapid progression indicators
            rapid_progression_signals = [
                "promoted", "advancement", "elevated", "progressed",
                "within 12 months", "within 18 months", "fast track",
            ]
            if any(signal in text for signal in rapid_progression_signals):
                score += 10

        # Check for leadership indicators even without explicit titles
        leadership_indicators = [
            "team lead", "managed team", "built team", "hired",
            "mentored", "coached", "trained reps",
        ]
        if any(indicator in text for indicator in leadership_indicators):
            score += 10

        return min(score, 100)

    def get_score_explanation(
        self,
        scores: Dict[str, float]
    ) -> Dict[str, str]:
        """
        Generate human-readable explanations for scores.
        """
        explanations = {}

        for category, score in scores.items():
            if category == "overall":
                continue

            if score >= 80:
                level = "Excellent"
            elif score >= 60:
                level = "Good"
            elif score >= 40:
                level = "Average"
            elif score >= 20:
                level = "Below Average"
            else:
                level = "Needs Improvement"

            explanations[category] = f"{level} ({score:.0f}/100)"

        return explanations

    def compare_resumes(
        self,
        resume_scores: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Compare multiple resumes and provide insights.
        """
        if not resume_scores:
            return {}

        # Calculate averages
        categories = [c.value for c in ScoreCategory]
        averages = {}

        for category in categories:
            values = [r.get(category, 0) for r in resume_scores]
            averages[category] = sum(values) / len(values) if values else 0

        # Find top performers per category
        top_per_category = {}
        for category in categories:
            sorted_resumes = sorted(
                enumerate(resume_scores),
                key=lambda x: x[1].get(category, 0),
                reverse=True
            )
            top_per_category[category] = [
                {"index": idx, "score": r.get(category, 0)}
                for idx, r in sorted_resumes[:3]
            ]

        return {
            "averages": averages,
            "top_performers": top_per_category,
            "total_resumes": len(resume_scores),
        }


# Singleton instances
_quick_scorer: Optional[QuickScorer] = None
_tech_sales_scorer: Optional[QuickScorer] = None


def get_scorer(weights: Optional[ScoringWeights] = None) -> QuickScorer:
    """Get the quick scorer singleton (generic scoring)."""
    global _quick_scorer
    if _quick_scorer is None:
        _quick_scorer = QuickScorer(weights)
    return _quick_scorer


def get_tech_sales_scorer(
    weights: Optional[TechSalesScoringWeights] = None
) -> QuickScorer:
    """
    Get the tech sales scorer singleton.
    Uses TechSalesScoringWeights with achievements, certifications, career progression.
    """
    global _tech_sales_scorer
    if _tech_sales_scorer is None:
        _tech_sales_scorer = QuickScorer(weights, use_tech_sales=True)
    return _tech_sales_scorer


async def score_resume(
    text: str,
    extracted_data: Optional[Dict[str, Any]] = None,
    job_keywords: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Convenience function to score a resume (generic scoring)."""
    scorer = get_scorer()
    return await scorer.score_resume(text, extracted_data, job_keywords)


async def score_tech_sales_resume(
    text: str,
    extracted_data: Optional[Dict[str, Any]] = None,
    job_keywords: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Score a tech sales resume with enhanced criteria.

    Uses TechSalesScoringWeights which includes:
    - achievements (18%): quota %, revenue, deals, rankings
    - certifications (8%): Salesforce, HubSpot, MEDDIC
    - career_progression (9%): SDR → AE → Senior AE trajectory

    Weights optimized based on 2025-2026 recruiter priorities.
    """
    scorer = get_tech_sales_scorer()
    return await scorer.score_resume(text, extracted_data, job_keywords)
