"""
Job Description Matching Service for Polished Resume Ranking System.
Premium feature for matching resumes against job descriptions.
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


# Common requirement patterns
REQUIREMENT_PATTERNS = {
    "years_experience": r"(\d+)\+?\s*(?:years?|yrs?)(?:\s*of)?\s*(?:experience|exp)?",
    "degree_required": r"(?:bachelor'?s?|master'?s?|phd|doctorate|degree)\s*(?:required|preferred)?",
    "certification": r"(?:certified|certification)\s+(?:in\s+)?(\w+)",
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

    @classmethod
    def parse(cls, job_description: str) -> Dict[str, Any]:
        """
        Parse a job description and extract structured requirements.

        Returns:
            Dictionary with extracted requirements
        """
        jd_lower = job_description.lower()

        return {
            "required_skills": cls._extract_skills(jd_lower),
            "experience_requirements": cls._extract_experience(jd_lower),
            "education_requirements": cls._extract_education(jd_lower),
            "keywords": cls._extract_keywords(jd_lower),
            "nice_to_haves": cls._extract_nice_to_haves(jd_lower),
        }

    @classmethod
    def _extract_skills(cls, text: str) -> List[str]:
        """Extract required skills from JD."""
        skills = set()

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


# Singleton instance
_jd_matcher: Optional[JDMatcher] = None


def get_matcher(weights: Optional[MatchWeights] = None) -> JDMatcher:
    """Get the JD matcher singleton."""
    global _jd_matcher
    if _jd_matcher is None:
        _jd_matcher = JDMatcher(weights)
    return _jd_matcher


async def match_resume(
    resume_text: str,
    resume_data: Dict[str, Any],
    job_description: str,
) -> Dict[str, Any]:
    """Convenience function to match a resume."""
    matcher = get_matcher()
    return await matcher.match_resume(resume_text, resume_data, job_description)
