"""
Quick Scoring Service for Polished Resume Ranking System.
Implements rule-based scoring for the free tier.
"""

from typing import Dict, List, Optional, Any, Tuple
import re
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


@dataclass
class ScoringWeights:
    """Configurable scoring weights."""
    experience: float = 0.25
    skills: float = 0.30
    education: float = 0.15
    formatting: float = 0.10
    keywords: float = 0.15
    contact_info: float = 0.05

    def to_dict(self) -> Dict[str, float]:
        return {
            "experience": self.experience,
            "skills": self.skills,
            "education": self.education,
            "formatting": self.formatting,
            "keywords": self.keywords,
            "contact_info": self.contact_info,
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


class QuickScorer:
    """
    Rule-based resume scoring service.
    Provides fast, deterministic scoring without LLM calls.
    """

    def __init__(self, weights: Optional[ScoringWeights] = None):
        self.weights = weights or ScoringWeights()

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

        # Calculate individual category scores
        scores = {
            ScoreCategory.EXPERIENCE.value: self._score_experience(text_lower, extracted),
            ScoreCategory.SKILLS.value: self._score_skills(text_lower, extracted),
            ScoreCategory.EDUCATION.value: self._score_education(text_lower, extracted),
            ScoreCategory.FORMATTING.value: self._score_formatting(text),
            ScoreCategory.KEYWORDS.value: self._score_keywords(text_lower, job_keywords),
            ScoreCategory.CONTACT_INFO.value: self._score_contact_info(extracted),
        }

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
        """Score based on work experience."""
        score = 0

        # Years of experience
        years = extracted.get("years_of_experience", 0) or 0
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

        # Find additional skills in text
        for skill in ALL_SKILLS:
            if skill in text:
                found_skills.add(skill)

        skill_count = len(found_skills)

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
        for category, skills in SKILL_CATEGORIES.items():
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


# Singleton instance
_quick_scorer: Optional[QuickScorer] = None


def get_scorer(weights: Optional[ScoringWeights] = None) -> QuickScorer:
    """Get the quick scorer singleton."""
    global _quick_scorer
    if _quick_scorer is None:
        _quick_scorer = QuickScorer(weights)
    return _quick_scorer


async def score_resume(
    text: str,
    extracted_data: Optional[Dict[str, Any]] = None,
    job_keywords: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Convenience function to score a resume."""
    scorer = get_scorer()
    return await scorer.score_resume(text, extracted_data, job_keywords)
