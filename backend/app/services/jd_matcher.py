"""
Job Description Matching Service for Polished Resume Ranking System.
Premium feature for matching resumes against job descriptions.

Enhanced for Tech Sales with role-specific matching and sales metrics awareness.
"""

from typing import Dict, List, Optional, Any, Tuple, Set
import re
from dataclasses import dataclass
from enum import Enum


class MatchCategory(str, Enum):
    """Matching categories."""
    SKILLS = "skills"
    EXPERIENCE = "experience"
    EDUCATION = "education"
    KEYWORDS = "keywords"
    REQUIREMENTS = "requirements"
    SALES_METRICS = "sales_metrics"
    METHODOLOGY = "methodology"


@dataclass
class MatchWeights:
    """Configurable matching weights."""
    skills: float = 0.35
    experience: float = 0.25
    education: float = 0.15
    keywords: float = 0.15
    requirements: float = 0.10

    def to_dict(self) -> Dict[str, float]:
        return {
            "skills": self.skills,
            "experience": self.experience,
            "education": self.education,
            "keywords": self.keywords,
            "requirements": self.requirements,
        }


@dataclass
class TechSalesMatchWeights:
    """Tech sales-specific matching weights."""
    quota_metrics: float = 0.25
    sales_tools: float = 0.20
    methodology: float = 0.15
    experience: float = 0.20
    keywords: float = 0.10
    soft_skills: float = 0.10

    def to_dict(self) -> Dict[str, float]:
        return {
            "quota_metrics": self.quota_metrics,
            "sales_tools": self.sales_tools,
            "methodology": self.methodology,
            "experience": self.experience,
            "keywords": self.keywords,
            "soft_skills": self.soft_skills,
        }


# Common requirement patterns
REQUIREMENT_PATTERNS = {
    "years_experience": r"(\d+)\+?\s*(?:years?|yrs?)(?:\s*of)?\s*(?:experience|exp)?",
    "degree_required": r"(?:bachelor'?s?|master'?s?|phd|doctorate|degree)\s*(?:required|preferred)?",
    "certification": r"(?:certified|certification)\s+(?:in\s+)?(\w+)",
}

# Tech Sales specific vocabularies
SALES_METHODOLOGIES = [
    "meddic", "meddpicc", "bant", "challenger", "spin", "sandler",
    "solution selling", "value selling", "command of message",
    "gap selling", "consultative selling", "target account selling",
]

SALES_TOOLS = {
    "crm": ["salesforce", "hubspot", "pipedrive", "dynamics", "zoho"],
    "engagement": ["outreach", "salesloft", "apollo", "lemlist", "reply.io"],
    "intelligence": ["gong", "chorus", "clari", "revenue.io", "wingman"],
    "prospecting": ["zoominfo", "linkedin sales navigator", "lusha", "apollo", "seamless.ai"],
    "productivity": ["calendly", "docusign", "pandadoc", "highspot", "seismic"],
}

SALES_METRICS_PATTERNS = {
    "quota": r"(\d+)%?\s*(?:of\s+)?quota|quota\s*(?:attainment|achievement)?\s*:?\s*(\d+)%",
    "revenue": r"\$[\d,]+(?:\s*[KMB])?(?:\s*(?:arr|mrr|revenue|closed))?",
    "deals": r"(\d+)\+?\s*(?:deals?|opportunities|accounts?)\s*(?:closed|won)?",
    "acv": r"(?:acv|average contract value)\s*(?:of\s*)?\$?[\d,]+[KMB]?",
    "pipeline": r"\$[\d,]+(?:\s*[KMB])?\s*(?:pipeline|opportunity)",
    "meetings": r"(\d+)\+?\s*(?:meetings?|demos?|calls?)\s*(?:booked|scheduled|per\s*(?:day|week|month))?",
    "nrr": r"(?:nrr|net revenue retention)\s*(?:of\s*)?(\d+)%",
    "churn": r"(?:churn|retention)\s*(?:rate\s*)?(?:of\s*)?(\d+(?:\.\d+)?)%",
}

ROLE_SPECIFIC_KEYWORDS = {
    "entry_sdr": {
        "must_have": ["cold calling", "prospecting", "outbound", "crm"],
        "nice_to_have": ["quota", "meetings booked", "salesforce", "email outreach"],
        "metrics": ["calls", "emails", "meetings booked", "ramp time"],
    },
    "sdr": {
        "must_have": ["sdr", "bdr", "prospecting", "cold calling", "quota"],
        "nice_to_have": ["outreach", "salesforce", "sql", "pipeline", "gong"],
        "metrics": ["meetings booked", "quota", "sqls", "conversion rate", "pipeline"],
    },
    "account_executive": {
        "must_have": ["account executive", "ae", "closing", "full cycle", "quota"],
        "nice_to_have": ["meddic", "discovery", "demo", "negotiation", "forecasting"],
        "metrics": ["quota attainment", "acv", "deals closed", "win rate", "sales cycle"],
    },
    "senior_ae": {
        "must_have": ["enterprise", "strategic", "complex sales", "c-suite"],
        "nice_to_have": ["meddpicc", "multi-stakeholder", "fortune 500", "value selling"],
        "metrics": ["enterprise deals", "deal size", "multi-year", "expansion"],
    },
    "account_manager": {
        "must_have": ["account manager", "csm", "retention", "renewal", "upsell"],
        "nice_to_have": ["nrr", "churn", "qbr", "expansion", "customer success"],
        "metrics": ["nrr", "grr", "churn rate", "expansion revenue", "retention"],
    },
    "sales_manager": {
        "must_have": ["sales manager", "leadership", "team", "coaching", "hiring"],
        "nice_to_have": ["forecast", "territory", "process", "onboarding", "mentoring"],
        "metrics": ["team quota", "team size", "rep retention", "ramp time"],
    },
}


class JDParser:
    """Parse and extract requirements from job descriptions."""

    # Skill extraction patterns
    SKILL_SECTION_PATTERNS = [
        r"(?:required|preferred|key|technical|must-have)\s*skills?[:\s]*([^.]+)",
        r"skills?\s*(?:required|needed|preferred)[:\s]*([^.]+)",
        r"(?:requirements?|qualifications?)[:\s]*([^.]+(?:experience|skills?))",
    ]

    # Experience patterns
    EXPERIENCE_PATTERNS = [
        r"(\d+)\+?\s*(?:years?|yrs?)(?:\s*of)?\s*(?:experience|exp)?\s*(?:in|with)?\s*([a-zA-Z\s,]+)?",
        r"(?:minimum|at least)\s*(\d+)\s*(?:years?|yrs?)",
        r"(\d+)-(\d+)\s*(?:years?|yrs?)\s*(?:of)?\s*(?:experience)?",
    ]

    # Education patterns
    EDUCATION_PATTERNS = [
        r"(bachelor'?s?|master'?s?|phd|doctorate|bs|ms|mba)\s*(?:degree)?\s*(?:in|of)?\s*([a-zA-Z\s]+)?",
        r"degree\s*(?:in|of)\s*([a-zA-Z\s]+)",
        r"(?:cs|computer science|engineering|mathematics)\s*(?:degree|background)",
    ]

    # Sales-specific patterns
    SALES_ROLE_PATTERNS = [
        r"(?:sdr|bdr|sales development|business development)\s*(?:rep(?:resentative)?)?",
        r"account\s*(?:executive|manager)",
        r"(?:inside|outside|enterprise|strategic)\s*sales",
        r"(?:sales|revenue)\s*(?:manager|director|vp)",
        r"customer\s*success\s*(?:manager)?",
    ]

    QUOTA_REQUIREMENT_PATTERNS = [
        r"track\s*record\s*(?:of\s*)?(?:exceeding|meeting|achieving)\s*quota",
        r"(?:consistently|proven)\s*(?:exceed(?:ed)?|achiev(?:ed)?|hit(?:ting)?)\s*quota",
        r"(\d+)%?\s*(?:to|of)\s*quota",
    ]

    @classmethod
    def parse(cls, job_description: str, is_tech_sales: bool = True) -> Dict[str, Any]:
        """
        Parse a job description and extract structured requirements.

        Args:
            job_description: The job description text
            is_tech_sales: Whether to use tech sales-specific parsing

        Returns:
            Dictionary with extracted requirements
        """
        jd_lower = job_description.lower()

        result = {
            "required_skills": cls._extract_skills(jd_lower, is_tech_sales),
            "experience_requirements": cls._extract_experience(jd_lower),
            "education_requirements": cls._extract_education(jd_lower),
            "keywords": cls._extract_keywords(jd_lower),
            "nice_to_haves": cls._extract_nice_to_haves(jd_lower),
        }

        # Add tech sales-specific parsing
        if is_tech_sales:
            result["sales_methodologies"] = cls._extract_sales_methodologies(jd_lower)
            result["sales_tools"] = cls._extract_sales_tools(jd_lower)
            result["detected_role"] = cls._detect_sales_role_type(jd_lower)
            result["quota_requirements"] = cls._extract_quota_requirements(jd_lower)

        return result

    @classmethod
    def _extract_quota_requirements(cls, text: str) -> Dict[str, Any]:
        """Extract quota-related requirements from JD."""
        result = {
            "requires_quota_achievement": False,
            "quota_percentage": None,
            "track_record_required": False,
        }

        # Check for quota achievement requirements
        for pattern in cls.QUOTA_REQUIREMENT_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result["requires_quota_achievement"] = True
                # Try to extract percentage if present
                groups = match.groups()
                for g in groups:
                    if g and g.isdigit():
                        result["quota_percentage"] = int(g)
                        break

        # Check for track record requirement
        if "track record" in text or "proven" in text or "demonstrated" in text:
            result["track_record_required"] = True

        return result

    @classmethod
    def _extract_skills(cls, text: str, is_tech_sales: bool = True) -> List[str]:
        """Extract required skills from JD."""
        skills = set()

        if is_tech_sales:
            # Tech Sales specific skills
            sales_skills = [
                # Sales tools
                "salesforce", "hubspot", "outreach", "salesloft", "gong", "chorus",
                "clari", "linkedin sales navigator", "zoominfo", "apollo", "lusha",
                "docusign", "pandadoc", "calendly", "highspot", "seismic",
                # Sales methodologies
                "meddic", "meddpicc", "bant", "challenger", "spin", "sandler",
                "solution selling", "value selling", "consultative selling",
                # Sales skills
                "cold calling", "prospecting", "discovery", "demo", "negotiation",
                "closing", "forecasting", "pipeline management", "account planning",
                "territory management", "contract negotiation", "objection handling",
                # Soft skills
                "communication", "presentation", "relationship building",
                "time management", "self-motivated", "competitive", "resilient",
            ]
            for skill in sales_skills:
                if skill in text:
                    skills.add(skill)
        else:
            # Common tech skills to look for
            tech_skills = [
                "python", "javascript", "typescript", "java", "c++", "c#", "go", "rust",
                "react", "angular", "vue", "node.js", "django", "flask", "fastapi",
                "aws", "azure", "gcp", "docker", "kubernetes", "terraform",
                "sql", "postgresql", "mysql", "mongodb", "redis", "elasticsearch",
                "git", "ci/cd", "agile", "scrum", "jira",
                "machine learning", "deep learning", "nlp", "data science",
                "rest api", "graphql", "microservices", "serverless",
            ]
            for skill in tech_skills:
                if skill in text:
                    skills.add(skill)

        # Try to extract from skill sections
        for pattern in cls.SKILL_SECTION_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                # Split by common delimiters
                parts = re.split(r'[,;/]|\sand\s|\sor\s', match)
                for part in parts:
                    part = part.strip()
                    if 2 < len(part) < 30:
                        skills.add(part.lower())

        return list(skills)

    @classmethod
    def _extract_sales_methodologies(cls, text: str) -> List[str]:
        """Extract sales methodologies mentioned in JD."""
        found = []
        for methodology in SALES_METHODOLOGIES:
            if methodology in text:
                found.append(methodology)
        return found

    @classmethod
    def _extract_sales_tools(cls, text: str) -> Dict[str, List[str]]:
        """Extract sales tools by category from JD."""
        found = {}
        for category, tools in SALES_TOOLS.items():
            category_tools = [tool for tool in tools if tool in text]
            if category_tools:
                found[category] = category_tools
        return found

    @classmethod
    def _detect_sales_role_type(cls, text: str) -> Optional[str]:
        """Detect what type of sales role is described in the JD."""
        text_lower = text.lower()

        # Check for specific role indicators
        if any(term in text_lower for term in ["sales manager", "sales director", "sales vp", "team lead"]):
            return "sales_manager"
        if any(term in text_lower for term in ["enterprise", "strategic account", "fortune 500"]):
            return "senior_ae"
        if any(term in text_lower for term in ["account manager", "customer success", "csm", "retention"]):
            return "account_manager"
        if any(term in text_lower for term in ["account executive", "ae", "full cycle", "closing"]):
            return "account_executive"
        if any(term in text_lower for term in ["sdr", "bdr", "sales development", "business development"]):
            years_match = re.search(r"(\d+)\+?\s*(?:years?|yrs?)", text_lower)
            if years_match and int(years_match.group(1)) < 2:
                return "entry_sdr"
            return "sdr"

        return None

    @classmethod
    def _extract_experience(cls, text: str) -> Dict[str, Any]:
        """Extract experience requirements."""
        result = {
            "min_years": None,
            "max_years": None,
            "areas": [],
        }

        for pattern in cls.EXPERIENCE_PATTERNS:
            matches = re.findall(pattern, text)
            for match in matches:
                if isinstance(match, tuple):
                    if len(match) >= 2 and match[0].isdigit():
                        years = int(match[0])
                        if result["min_years"] is None or years < result["min_years"]:
                            result["min_years"] = years
                        if match[1] and len(match[1].strip()) > 2:
                            result["areas"].append(match[1].strip())
                elif match.isdigit():
                    years = int(match)
                    if result["min_years"] is None or years < result["min_years"]:
                        result["min_years"] = years

        return result

    @classmethod
    def _extract_education(cls, text: str) -> Dict[str, Any]:
        """Extract education requirements."""
        result = {
            "degree_level": None,
            "fields": [],
            "required": False,
        }

        degree_levels = {
            "phd": 4, "doctorate": 4,
            "master": 3, "masters": 3, "ms": 3, "mba": 3,
            "bachelor": 2, "bachelors": 2, "bs": 2,
            "associate": 1,
        }

        for pattern in cls.EDUCATION_PATTERNS:
            matches = re.findall(pattern, text)
            for match in matches:
                if isinstance(match, tuple):
                    degree = match[0].lower().strip("'s")
                    if degree in degree_levels:
                        if result["degree_level"] is None or degree_levels[degree] > degree_levels.get(result["degree_level"], 0):
                            result["degree_level"] = degree
                    if len(match) > 1 and match[1]:
                        result["fields"].append(match[1].strip())

        # Check if degree is required
        if "required" in text and any(d in text for d in degree_levels):
            result["required"] = True

        return result

    @classmethod
    def _extract_keywords(cls, text: str) -> List[str]:
        """Extract important keywords from JD."""
        keywords = []

        # Common important keywords
        important_keywords = [
            "leadership", "teamwork", "communication", "problem-solving",
            "startup", "enterprise", "scale", "growth", "innovation",
            "remote", "hybrid", "on-site", "full-time", "contract",
            "senior", "lead", "principal", "staff", "manager",
        ]

        for keyword in important_keywords:
            if keyword in text:
                keywords.append(keyword)

        return keywords

    @classmethod
    def _extract_nice_to_haves(cls, text: str) -> List[str]:
        """Extract nice-to-have/preferred qualifications."""
        nice_to_haves = []

        # Look for nice-to-have sections
        patterns = [
            r"(?:nice to have|preferred|bonus|plus)[:\s]*([^.]+)",
            r"(?:ideally|preferably)[,\s]+([^.]+)",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                parts = re.split(r'[,;]|\sand\s', match)
                for part in parts:
                    part = part.strip()
                    if 3 < len(part) < 50:
                        nice_to_haves.append(part)

        return nice_to_haves[:10]  # Limit to 10


class TechSalesJDMatcher:
    """
    Tech Sales-specific JD Matcher providing detailed match analysis.
    Includes role-specific matching, sales metrics awareness, and methodology alignment.
    """

    def __init__(self, weights: Optional[TechSalesMatchWeights] = None):
        self.weights = weights or TechSalesMatchWeights()
        self.parser = JDParser()

    async def match_resume(
        self,
        resume_text: str,
        resume_data: Dict[str, Any],
        job_description: str,
        target_role: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Match a tech sales resume against a job description.

        Args:
            resume_text: Raw resume text
            resume_data: Extracted resume data
            job_description: Job description text
            target_role: Optional target sales role for more specific matching

        Returns:
            Detailed match results with score and recommendations
        """
        # Parse job description with tech sales focus
        jd_requirements = self.parser.parse(job_description, is_tech_sales=True)

        # Use detected role if not provided
        if not target_role:
            target_role = jd_requirements.get("detected_role")

        resume_lower = resume_text.lower()
        resume_skills = set(s.lower() for s in resume_data.get("skills", []))

        # Calculate tech sales-specific category matches
        quota_match = self._match_quota_metrics(resume_lower, jd_requirements)
        tools_match = self._match_sales_tools(resume_lower, resume_skills, jd_requirements)
        methodology_match = self._match_methodologies(resume_lower, jd_requirements)
        experience_match = self._match_experience(resume_data, jd_requirements, target_role)
        keywords_match = self._match_keywords(resume_lower, jd_requirements, target_role)
        soft_skills_match = self._match_soft_skills(resume_lower)

        # Calculate weighted score
        weights = self.weights.to_dict()
        match_score = (
            quota_match["score"] * weights["quota_metrics"] +
            tools_match["score"] * weights["sales_tools"] +
            methodology_match["score"] * weights["methodology"] +
            experience_match["score"] * weights["experience"] +
            keywords_match["score"] * weights["keywords"] +
            soft_skills_match["score"] * weights["soft_skills"]
        )

        # Generate gaps and recommendations
        gaps = self._identify_gaps(
            quota_match, tools_match, methodology_match,
            experience_match, keywords_match, jd_requirements, target_role
        )

        keywords_to_add = self._get_keywords_to_add(
            resume_lower, jd_requirements, target_role
        )

        recommendations = self._generate_recommendations(
            match_score, gaps, target_role, jd_requirements
        )

        return {
            "match_score": round(match_score, 0),
            "category_scores": {
                "quota_metrics": quota_match["score"],
                "sales_tools": tools_match["score"],
                "methodology": methodology_match["score"],
                "experience": experience_match["score"],
                "keywords": keywords_match["score"],
                "soft_skills": soft_skills_match["score"],
            },
            "matching_requirements": keywords_match.get("matched", []) + methodology_match.get("matched", []),
            "gaps": gaps,
            "keywords_to_add": keywords_to_add,
            "keywords_present": keywords_match.get("matched", []),
            "tailored_suggestions": recommendations,
            "experience_match": experience_match["details"]["meets_requirement"],
            "skills_alignment": tools_match.get("by_category", {}),
            "detected_role": jd_requirements.get("detected_role"),
            "quota_metrics_found": quota_match.get("metrics_found", {}),
            "methodologies_found": methodology_match.get("matched", []),
        }

    def _match_quota_metrics(
        self,
        resume_text: str,
        jd_requirements: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Match quota and sales metrics from resume."""
        metrics_found = {}
        score = 50  # Base score

        # Look for sales metrics in resume
        for metric_type, pattern in SALES_METRICS_PATTERNS.items():
            matches = re.findall(pattern, resume_text, re.IGNORECASE)
            if matches:
                metrics_found[metric_type] = matches[:3]
                score += 10  # Bonus for each metric type found

        # Extra points if JD requires quota achievement and resume shows it
        quota_req = jd_requirements.get("quota_requirements", {})
        if quota_req.get("requires_quota_achievement"):
            if metrics_found.get("quota"):
                score += 15
            elif any(term in resume_text for term in ["exceeded quota", "achieved quota", "100%", "110%", "120%"]):
                score += 15

        return {
            "score": min(score, 100),
            "metrics_found": metrics_found,
        }

    def _match_sales_tools(
        self,
        resume_text: str,
        resume_skills: Set[str],
        jd_requirements: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Match sales tools from resume against JD."""
        required_tools = jd_requirements.get("sales_tools", {})
        matched_by_category = {}
        missing_by_category = {}
        total_required = 0
        total_matched = 0

        # Check each category
        for category, tools in required_tools.items():
            matched = []
            missing = []
            for tool in tools:
                if tool in resume_text or any(tool in s for s in resume_skills):
                    matched.append(tool)
                else:
                    missing.append(tool)
            matched_by_category[category] = matched
            missing_by_category[category] = missing
            total_required += len(tools)
            total_matched += len(matched)

        # Also check for tools mentioned in resume but not specifically required
        extra_tools = []
        for category_tools in SALES_TOOLS.values():
            for tool in category_tools:
                if tool in resume_text and tool not in [t for tools in required_tools.values() for t in tools]:
                    extra_tools.append(tool)

        # Calculate score
        if total_required > 0:
            base_score = (total_matched / total_required) * 80
        else:
            # No specific tools required, check if resume has any sales tools
            base_score = min(len(extra_tools) * 15, 60)

        # Bonus for CRM proficiency (always valuable)
        if any(crm in resume_text for crm in SALES_TOOLS["crm"]):
            base_score += 10

        return {
            "score": min(base_score, 100),
            "by_category": {
                "matched": matched_by_category,
                "missing": missing_by_category,
            },
            "extra_tools": extra_tools[:5],
        }

    def _match_methodologies(
        self,
        resume_text: str,
        jd_requirements: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Match sales methodologies from resume."""
        required_methodologies = jd_requirements.get("sales_methodologies", [])
        matched = []
        missing = []

        for methodology in required_methodologies:
            if methodology in resume_text:
                matched.append(methodology)
            else:
                missing.append(methodology)

        # Also find any methodologies in resume not in JD
        extra = []
        for methodology in SALES_METHODOLOGIES:
            if methodology in resume_text and methodology not in required_methodologies:
                extra.append(methodology)

        # Calculate score
        if required_methodologies:
            score = (len(matched) / len(required_methodologies)) * 80
            # Bonus for having extra methodologies
            score += min(len(extra) * 5, 20)
        else:
            # No specific requirement, bonus for having any
            score = 50 + min(len(extra) * 10, 40)

        return {
            "score": min(score, 100),
            "matched": matched,
            "missing": missing,
            "extra": extra,
        }

    def _match_experience(
        self,
        resume_data: Dict[str, Any],
        jd_requirements: Dict[str, Any],
        target_role: Optional[str],
    ) -> Dict[str, Any]:
        """Match experience requirements."""
        resume_years = resume_data.get("years_of_experience", 0) or 0
        exp_req = jd_requirements.get("experience_requirements", {})
        required_years = exp_req.get("min_years") or 0

        # Adjust based on target role expectations
        role_years_map = {
            "entry_sdr": (0, 1),
            "sdr": (1, 3),
            "account_executive": (2, 5),
            "senior_ae": (5, 15),
            "account_manager": (2, 10),
            "sales_manager": (5, 20),
        }

        if target_role and target_role in role_years_map:
            role_min, role_max = role_years_map[target_role]
            # Use the more specific requirement
            if required_years == 0:
                required_years = role_min

        # Calculate score
        if required_years == 0:
            score = 75
            meets_requirement = True
        elif resume_years >= required_years:
            score = 100
            meets_requirement = True
        else:
            ratio = resume_years / required_years
            score = ratio * 80
            meets_requirement = False

        return {
            "score": round(score, 2),
            "details": {
                "resume_years": resume_years,
                "required_years": required_years,
                "meets_requirement": meets_requirement,
            }
        }

    def _match_keywords(
        self,
        resume_text: str,
        jd_requirements: Dict[str, Any],
        target_role: Optional[str],
    ) -> Dict[str, Any]:
        """Match keywords from JD and role-specific keywords."""
        matched = []
        missing = []

        # Get JD keywords
        jd_keywords = set(jd_requirements.get("keywords", []))

        # Add role-specific keywords if we know the role
        if target_role and target_role in ROLE_SPECIFIC_KEYWORDS:
            role_kw = ROLE_SPECIFIC_KEYWORDS[target_role]
            jd_keywords.update(role_kw.get("must_have", []))

        # Check matches
        for kw in jd_keywords:
            if kw.lower() in resume_text:
                matched.append(kw)
            else:
                missing.append(kw)

        # Calculate score
        if jd_keywords:
            score = (len(matched) / len(jd_keywords)) * 100
        else:
            score = 75

        return {
            "score": round(score, 2),
            "matched": matched,
            "missing": missing[:10],
        }

    def _match_soft_skills(self, resume_text: str) -> Dict[str, Any]:
        """Match soft skills important for sales."""
        soft_skills = [
            "communication", "presentation", "negotiation", "relationship",
            "team player", "self-motivated", "driven", "competitive",
            "resilient", "organized", "detail-oriented", "collaborative",
        ]

        found = [s for s in soft_skills if s in resume_text]
        score = min(len(found) * 15, 100)

        return {
            "score": score,
            "found": found,
        }

    def _identify_gaps(
        self,
        quota_match: Dict,
        tools_match: Dict,
        methodology_match: Dict,
        experience_match: Dict,
        keywords_match: Dict,
        jd_requirements: Dict,
        target_role: Optional[str],
    ) -> List[str]:
        """Identify gaps that could cause rejection."""
        gaps = []

        # Experience gap
        if not experience_match["details"]["meets_requirement"]:
            required = experience_match["details"]["required_years"]
            actual = experience_match["details"]["resume_years"]
            gaps.append(f"Experience: {actual} years vs {required}+ required")

        # Methodology gaps
        if methodology_match.get("missing"):
            gaps.append(f"Missing methodology: {', '.join(methodology_match['missing'][:2])}")

        # Tool gaps
        missing_tools = tools_match.get("by_category", {}).get("missing", {})
        for category, tools in missing_tools.items():
            if tools:
                gaps.append(f"Missing {category} tool(s): {', '.join(tools[:2])}")

        # Quota/metrics gap
        if jd_requirements.get("quota_requirements", {}).get("requires_quota_achievement"):
            if not quota_match.get("metrics_found", {}).get("quota"):
                gaps.append("No quota attainment metrics shown")

        # Keyword gaps
        if keywords_match.get("missing"):
            critical_missing = keywords_match["missing"][:3]
            if critical_missing:
                gaps.append(f"Missing keywords: {', '.join(critical_missing)}")

        return gaps[:6]  # Limit to top 6 gaps

    def _get_keywords_to_add(
        self,
        resume_text: str,
        jd_requirements: Dict[str, Any],
        target_role: Optional[str],
    ) -> List[str]:
        """Get prioritized keywords to add to resume."""
        keywords_to_add = []

        # Missing skills from JD
        for skill in jd_requirements.get("required_skills", []):
            if skill.lower() not in resume_text:
                keywords_to_add.append(skill)

        # Missing methodologies
        for method in jd_requirements.get("sales_methodologies", []):
            if method not in resume_text:
                keywords_to_add.append(method.upper())

        # Role-specific keywords
        if target_role and target_role in ROLE_SPECIFIC_KEYWORDS:
            role_kw = ROLE_SPECIFIC_KEYWORDS[target_role]
            for kw in role_kw.get("must_have", []):
                if kw.lower() not in resume_text and kw not in keywords_to_add:
                    keywords_to_add.append(kw)

        return keywords_to_add[:10]

    def _generate_recommendations(
        self,
        match_score: float,
        gaps: List[str],
        target_role: Optional[str],
        jd_requirements: Dict[str, Any],
    ) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []

        # Score-based recommendation header
        if match_score >= 80:
            recommendations.append("Strong match! Minor refinements recommended:")
        elif match_score >= 60:
            recommendations.append("Good potential. Key improvements needed:")
        elif match_score >= 40:
            recommendations.append("Moderate match. Significant gaps to address:")
        else:
            recommendations.append("Weak match for this role. Consider:")

        # Gap-based recommendations
        for gap in gaps:
            if "Experience" in gap:
                recommendations.append("Highlight transferable experience and quick ramp-up potential")
            elif "methodology" in gap.lower():
                if "meddic" in gap.lower():
                    recommendations.append("Add MEDDIC/MEDDPICC if you've used it - critical for enterprise sales")
                else:
                    recommendations.append("Include any sales methodologies you've been trained on")
            elif "tool" in gap.lower():
                recommendations.append("List all sales tools you're proficient with, including CRM experience")
            elif "quota" in gap.lower():
                recommendations.append("Add specific quota attainment percentages (e.g., '120% of quota')")
            elif "keyword" in gap.lower():
                recommendations.append("Mirror key terms from the job description in your experience")

        # Role-specific recommendations
        if target_role == "entry_sdr":
            recommendations.append("Emphasize coachability, drive, and any customer-facing experience")
        elif target_role == "sdr":
            recommendations.append("Quantify activity metrics: calls/day, meetings booked, SQL conversion")
        elif target_role in ["account_executive", "senior_ae"]:
            recommendations.append("Include deal sizes, win rates, and sales cycle length")
        elif target_role == "account_manager":
            recommendations.append("Highlight NRR, churn reduction, and expansion revenue metrics")
        elif target_role == "sales_manager":
            recommendations.append("Show team size managed, team quota attainment, and rep development")

        return recommendations[:6]


class JDMatcher:
    """
    Service for matching resumes against job descriptions.
    Premium feature providing detailed match analysis.
    """

    def __init__(self, weights: Optional[MatchWeights] = None):
        self.weights = weights or MatchWeights()
        self.parser = JDParser()

    async def match_resume(
        self,
        resume_text: str,
        resume_data: Dict[str, Any],
        job_description: str,
    ) -> Dict[str, Any]:
        """
        Match a resume against a job description.

        Args:
            resume_text: Raw resume text
            resume_data: Extracted resume data
            job_description: Job description text

        Returns:
            Match results with score and details
        """
        # Parse job description
        jd_requirements = self.parser.parse(job_description)

        resume_lower = resume_text.lower()
        resume_skills = set(s.lower() for s in resume_data.get("skills", []))

        # Calculate category matches
        skills_match = self._match_skills(
            resume_skills,
            jd_requirements["required_skills"]
        )

        experience_match = self._match_experience(
            resume_data,
            jd_requirements["experience_requirements"]
        )

        education_match = self._match_education(
            resume_lower,
            resume_data,
            jd_requirements["education_requirements"]
        )

        keywords_match = self._match_keywords(
            resume_lower,
            jd_requirements["keywords"]
        )

        requirements_match = self._match_requirements(
            resume_lower,
            resume_skills,
            jd_requirements
        )

        # Calculate weighted score
        weights = self.weights.to_dict()
        match_score = (
            skills_match["score"] * weights["skills"] +
            experience_match["score"] * weights["experience"] +
            education_match["score"] * weights["education"] +
            keywords_match["score"] * weights["keywords"] +
            requirements_match["score"] * weights["requirements"]
        )

        # Generate recommendation
        recommendation = self._generate_recommendation(
            match_score,
            skills_match,
            experience_match,
            education_match,
        )

        return {
            "match_score": round(match_score, 2),
            "category_scores": {
                "skills": skills_match["score"],
                "experience": experience_match["score"],
                "education": education_match["score"],
                "keywords": keywords_match["score"],
                "requirements": requirements_match["score"],
            },
            "matched_skills": skills_match["matched"],
            "missing_skills": skills_match["missing"],
            "experience_match": experience_match["details"],
            "education_match": education_match["details"],
            "keyword_matches": keywords_match["matched"],
            "recommendation": recommendation,
            "nice_to_haves_matched": self._check_nice_to_haves(
                resume_lower,
                jd_requirements.get("nice_to_haves", [])
            ),
        }

    def _match_skills(
        self,
        resume_skills: Set[str],
        required_skills: List[str]
    ) -> Dict[str, Any]:
        """Match resume skills against required skills."""
        if not required_skills:
            return {"score": 75, "matched": [], "missing": []}

        required_set = set(s.lower() for s in required_skills)

        matched = list(resume_skills.intersection(required_set))
        missing = list(required_set - resume_skills)

        if required_set:
            match_ratio = len(matched) / len(required_set)
        else:
            match_ratio = 0.5

        # Score: 0-100 based on match ratio
        score = match_ratio * 100

        # Bonus for having extra relevant skills
        extra_skills = resume_skills - required_set
        if extra_skills and match_ratio >= 0.5:
            score = min(score + len(extra_skills) * 2, 100)

        return {
            "score": round(score, 2),
            "matched": matched,
            "missing": missing,
            "extra": list(extra_skills)[:10],
        }

    def _match_experience(
        self,
        resume_data: Dict[str, Any],
        experience_req: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Match resume experience against requirements."""
        resume_years = resume_data.get("years_of_experience", 0) or 0
        required_years = experience_req.get("min_years") or 0

        # Calculate score
        if required_years == 0:
            score = 75  # No specific requirement
            meets_requirement = True
        elif resume_years >= required_years:
            score = 100
            meets_requirement = True
            # Bonus for exceeding (but cap at 100)
            if resume_years > required_years + 3:
                score = 100
        else:
            # Partial credit
            ratio = resume_years / required_years if required_years > 0 else 0
            score = ratio * 80
            meets_requirement = False

        return {
            "score": round(score, 2),
            "details": {
                "resume_years": resume_years,
                "required_years": required_years,
                "meets_requirement": meets_requirement,
            }
        }

    def _match_education(
        self,
        resume_text: str,
        resume_data: Dict[str, Any],
        education_req: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Match resume education against requirements."""
        degree_levels = {
            "phd": 4, "doctorate": 4,
            "master": 3, "masters": 3, "ms": 3, "mba": 3,
            "bachelor": 2, "bachelors": 2, "bs": 2,
            "associate": 1,
        }

        required_level = education_req.get("degree_level")
        required_level_num = degree_levels.get(required_level, 0) if required_level else 0

        # Find resume's education level
        resume_level = None
        resume_level_num = 0

        for level, num in degree_levels.items():
            if level in resume_text:
                if num > resume_level_num:
                    resume_level_num = num
                    resume_level = level

        # Calculate score
        if required_level_num == 0:
            score = 80  # No specific requirement
            meets_requirement = True
        elif resume_level_num >= required_level_num:
            score = 100
            meets_requirement = True
        elif resume_level_num > 0:
            # Partial credit
            score = (resume_level_num / required_level_num) * 70
            meets_requirement = False
        else:
            score = 30
            meets_requirement = False

        # Check field match
        required_fields = education_req.get("fields", [])
        field_match = any(
            f.lower() in resume_text
            for f in required_fields
        ) if required_fields else True

        if field_match and score < 100:
            score = min(score + 15, 100)

        return {
            "score": round(score, 2),
            "details": {
                "resume_level": resume_level,
                "required_level": required_level,
                "meets_requirement": meets_requirement,
                "field_match": field_match,
            }
        }

    def _match_keywords(
        self,
        resume_text: str,
        keywords: List[str]
    ) -> Dict[str, Any]:
        """Match resume against JD keywords."""
        if not keywords:
            return {"score": 75, "matched": []}

        matched = [kw for kw in keywords if kw.lower() in resume_text]
        match_ratio = len(matched) / len(keywords) if keywords else 0

        return {
            "score": round(match_ratio * 100, 2),
            "matched": matched,
        }

    def _match_requirements(
        self,
        resume_text: str,
        resume_skills: Set[str],
        jd_requirements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Overall requirements match."""
        scores = []

        # Check required skills coverage
        required_skills = jd_requirements.get("required_skills", [])
        if required_skills:
            skill_coverage = len(resume_skills.intersection(set(s.lower() for s in required_skills))) / len(required_skills)
            scores.append(skill_coverage * 100)

        # Check experience
        exp_req = jd_requirements.get("experience_requirements", {})
        min_years = exp_req.get("min_years", 0)
        if min_years:
            # Look for years in resume
            years_match = re.search(r'(\d+)\+?\s*years?', resume_text)
            if years_match:
                resume_years = int(years_match.group(1))
                if resume_years >= min_years:
                    scores.append(100)
                else:
                    scores.append((resume_years / min_years) * 80)

        if scores:
            return {"score": round(sum(scores) / len(scores), 2)}
        return {"score": 70}

    def _check_nice_to_haves(
        self,
        resume_text: str,
        nice_to_haves: List[str]
    ) -> List[str]:
        """Check which nice-to-haves the resume matches."""
        return [nth for nth in nice_to_haves if nth.lower() in resume_text]

    def _generate_recommendation(
        self,
        match_score: float,
        skills_match: Dict,
        experience_match: Dict,
        education_match: Dict,
    ) -> str:
        """Generate a hiring recommendation."""
        if match_score >= 85:
            return "Strong Match - Highly recommended for interview"
        elif match_score >= 70:
            if skills_match["missing"]:
                missing = ", ".join(skills_match["missing"][:3])
                return f"Good Match - Consider interviewing. Missing skills: {missing}"
            return "Good Match - Recommended for interview"
        elif match_score >= 55:
            details = experience_match.get("details", {})
            if not details.get("meets_requirement"):
                return "Moderate Match - Experience below requirements"
            return "Moderate Match - May be suitable for junior roles"
        elif match_score >= 40:
            return "Weak Match - Significant gaps in requirements"
        else:
            return "Poor Match - Does not meet key requirements"

    async def batch_match(
        self,
        resumes: List[Dict[str, Any]],
        job_description: str,
    ) -> List[Dict[str, Any]]:
        """
        Match multiple resumes against a job description.

        Returns list of match results sorted by score.
        """
        results = []

        for resume in resumes:
            match_result = await self.match_resume(
                resume.get("text", ""),
                resume.get("extracted_data", {}),
                job_description,
            )
            match_result["resume_id"] = resume.get("resume_id")
            results.append(match_result)

        # Sort by match score
        results.sort(key=lambda x: x["match_score"], reverse=True)

        return results


# Singleton instances
_jd_matcher: Optional[JDMatcher] = None
_tech_sales_matcher: Optional[TechSalesJDMatcher] = None


def get_matcher(weights: Optional[MatchWeights] = None) -> JDMatcher:
    """Get the JD matcher singleton."""
    global _jd_matcher
    if _jd_matcher is None:
        _jd_matcher = JDMatcher(weights)
    return _jd_matcher


def get_tech_sales_matcher(weights: Optional[TechSalesMatchWeights] = None) -> TechSalesJDMatcher:
    """Get the tech sales JD matcher singleton."""
    global _tech_sales_matcher
    if _tech_sales_matcher is None:
        _tech_sales_matcher = TechSalesJDMatcher(weights)
    return _tech_sales_matcher


async def match_resume(
    resume_text: str,
    resume_data: Dict[str, Any],
    job_description: str,
) -> Dict[str, Any]:
    """Convenience function to match a resume."""
    matcher = get_matcher()
    return await matcher.match_resume(resume_text, resume_data, job_description)


async def match_tech_sales_resume(
    resume_text: str,
    resume_data: Dict[str, Any],
    job_description: str,
    target_role: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Convenience function to match a tech sales resume.

    Args:
        resume_text: Raw resume text
        resume_data: Extracted resume data
        job_description: Job description text
        target_role: Optional target sales role

    Returns:
        Detailed match results with tech sales-specific analysis
    """
    matcher = get_tech_sales_matcher()
    return await matcher.match_resume(
        resume_text, resume_data, job_description, target_role
    )


def parse_job_description(job_description: str, is_tech_sales: bool = True) -> Dict[str, Any]:
    """
    Parse a job description and extract requirements.

    Args:
        job_description: Job description text
        is_tech_sales: Whether to use tech sales-specific parsing

    Returns:
        Extracted requirements dictionary
    """
    return JDParser.parse(job_description, is_tech_sales)
