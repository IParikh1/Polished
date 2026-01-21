"""
Batch Processor Service for Polished Resume Ranking System.
Handles batch processing, resume parsing, and scoring orchestration.
"""

import asyncio
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
import io
import re
from concurrent.futures import ThreadPoolExecutor

from ..models.batch_schemas import (
    BatchStatus,
    ResumeStatus,
    PremiumFeature,
)
from .aws_store import get_store, AWSStore


# Try to import PDF/document parsing libraries
try:
    import PyPDF2
    HAS_PYPDF2 = True
except ImportError:
    HAS_PYPDF2 = False

try:
    from docx import Document
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False


class ResumeParser:
    """Parse resume content from various file formats."""

    @staticmethod
    def parse_pdf(content: bytes) -> str:
        """Extract text from PDF."""
        if not HAS_PYPDF2:
            return "[PDF parsing requires PyPDF2]"

        try:
            pdf_file = io.BytesIO(content)
            reader = PyPDF2.PdfReader(pdf_file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text.strip()
        except Exception as e:
            return f"[Error parsing PDF: {e}]"

    @staticmethod
    def parse_docx(content: bytes) -> str:
        """Extract text from DOCX."""
        if not HAS_DOCX:
            return "[DOCX parsing requires python-docx]"

        try:
            doc_file = io.BytesIO(content)
            doc = Document(doc_file)
            text = "\n".join([para.text for para in doc.paragraphs])
            return text.strip()
        except Exception as e:
            return f"[Error parsing DOCX: {e}]"

    @staticmethod
    def parse_text(content: bytes) -> str:
        """Extract text from plain text file."""
        try:
            return content.decode("utf-8", errors="ignore").strip()
        except Exception as e:
            return f"[Error parsing text: {e}]"

    @classmethod
    def parse(cls, content: bytes, filename: str) -> str:
        """Parse resume based on file extension."""
        ext = filename.lower().split(".")[-1]

        if ext == "pdf":
            return cls.parse_pdf(content)
        elif ext in ["docx"]:
            return cls.parse_docx(content)
        elif ext in ["doc"]:
            return "[DOC format requires additional libraries]"
        elif ext in ["txt", "rtf"]:
            return cls.parse_text(content)
        else:
            return cls.parse_text(content)


class ResumeExtractor:
    """Extract structured data from resume text."""

    # Common patterns
    EMAIL_PATTERN = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    PHONE_PATTERN = r"[\+]?[(]?[0-9]{1,3}[)]?[-\s\.]?[(]?[0-9]{1,3}[)]?[-\s\.]?[0-9]{3,4}[-\s\.]?[0-9]{3,4}"
    LINKEDIN_PATTERN = r"linkedin\.com/in/[\w-]+"

    # Common skills keywords
    TECH_SKILLS = [
        "python", "javascript", "typescript", "java", "c++", "c#", "go", "rust",
        "react", "angular", "vue", "node.js", "django", "flask", "fastapi",
        "aws", "azure", "gcp", "docker", "kubernetes", "terraform",
        "sql", "postgresql", "mysql", "mongodb", "redis", "elasticsearch",
        "git", "ci/cd", "jenkins", "github actions", "agile", "scrum",
        "machine learning", "deep learning", "nlp", "computer vision",
        "html", "css", "sass", "tailwind", "graphql", "rest api",
    ]

    # Education keywords
    EDUCATION_KEYWORDS = [
        "bachelor", "master", "phd", "doctorate", "degree", "university",
        "college", "institute", "bs", "ms", "mba", "b.s.", "m.s.",
        "computer science", "engineering", "mathematics", "physics",
    ]

    @classmethod
    def extract(cls, text: str) -> Dict[str, Any]:
        """Extract structured data from resume text."""
        text_lower = text.lower()

        # Extract email
        email_match = re.search(cls.EMAIL_PATTERN, text)
        email = email_match.group(0) if email_match else None

        # Extract phone
        phone_match = re.search(cls.PHONE_PATTERN, text)
        phone = phone_match.group(0) if phone_match else None

        # Extract name (usually first line or near email)
        name = cls._extract_name(text)

        # Extract skills
        skills = cls._extract_skills(text_lower)

        # Extract experience (years)
        years_exp = cls._extract_years_experience(text_lower)

        # Extract education
        education = cls._extract_education(text_lower)

        # Extract summary (first paragraph-like content)
        summary = cls._extract_summary(text)

        return {
            "name": name,
            "email": email,
            "phone": phone,
            "skills": skills,
            "years_of_experience": years_exp,
            "education": education,
            "summary": summary,
            "raw_length": len(text),
        }

    @classmethod
    def _extract_name(cls, text: str) -> Optional[str]:
        """Extract candidate name from resume."""
        lines = text.strip().split("\n")
        for line in lines[:5]:  # Check first 5 lines
            line = line.strip()
            # Skip empty lines and common headers
            if not line or len(line) < 3:
                continue
            if any(kw in line.lower() for kw in ["resume", "cv", "curriculum"]):
                continue
            # Skip lines with email/phone
            if "@" in line or re.search(cls.PHONE_PATTERN, line):
                continue
            # Likely a name if it's 2-4 words
            words = line.split()
            if 2 <= len(words) <= 4 and all(w[0].isupper() for w in words if w):
                return line
        return None

    @classmethod
    def _extract_skills(cls, text: str) -> List[str]:
        """Extract skills from resume text."""
        found_skills = []
        for skill in cls.TECH_SKILLS:
            if skill in text:
                found_skills.append(skill)
        return found_skills

    @classmethod
    def _extract_years_experience(cls, text: str) -> Optional[int]:
        """Extract years of experience from resume."""
        patterns = [
            r"(\d+)\+?\s*years?\s*(?:of\s*)?experience",
            r"experience[:\s]*(\d+)\+?\s*years?",
            r"(\d+)\+?\s*years?\s*(?:in|of)\s*(?:software|development|engineering)",
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return int(match.group(1))

        return None

    @classmethod
    def _extract_education(cls, text: str) -> List[Dict[str, str]]:
        """Extract education information."""
        education = []

        # Look for degree patterns
        degree_patterns = [
            r"(bachelor'?s?|master'?s?|phd|doctorate|mba|b\.?s\.?|m\.?s\.?)\s*(?:in|of)?\s*([a-z\s]+?)(?:\s*from|\s*at|\s*,|\s*\n)",
            r"(university|college|institute)\s+(?:of\s+)?([a-z\s]+)",
        ]

        for pattern in degree_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                education.append({
                    "degree": match.group(1).strip(),
                    "field": match.group(2).strip() if match.lastindex >= 2 else None
                })

        return education[:3]  # Limit to 3 entries

    @classmethod
    def _extract_summary(cls, text: str) -> Optional[str]:
        """Extract professional summary."""
        lines = text.split("\n")

        # Look for summary section
        in_summary = False
        summary_lines = []

        for line in lines:
            line_lower = line.lower().strip()

            if any(kw in line_lower for kw in ["summary", "objective", "profile", "about"]):
                in_summary = True
                continue

            if in_summary:
                if any(kw in line_lower for kw in ["experience", "education", "skills", "work"]):
                    break
                if line.strip():
                    summary_lines.append(line.strip())
                    if len(summary_lines) >= 3:
                        break

        if summary_lines:
            return " ".join(summary_lines)[:500]

        return None


class BatchProcessor:
    """Process batches of resumes."""

    def __init__(self):
        self.store: AWSStore = get_store()
        self.parser = ResumeParser()
        self.extractor = ResumeExtractor()
        self.executor = ThreadPoolExecutor(max_workers=10)
        self._processing_batches: Dict[str, bool] = {}

    async def process_batch(
        self,
        batch_id: str,
        scoring_callback: Optional[Callable] = None,
        jd_matching_callback: Optional[Callable] = None,
        deep_analysis_callback: Optional[Callable] = None,
    ) -> Dict[str, Any]:
        """
        Process all resumes in a batch.

        Args:
            batch_id: The batch to process
            scoring_callback: Function to score resumes
            jd_matching_callback: Function for JD matching (premium)
            deep_analysis_callback: Function for deep analysis (premium)

        Returns:
            Processing results summary
        """
        # Check if already processing
        if self._processing_batches.get(batch_id):
            return {"error": "Batch is already being processed"}

        self._processing_batches[batch_id] = True

        try:
            # Get batch
            batch = await self.store.get_batch(batch_id)
            if not batch:
                return {"error": "Batch not found"}

            # Update status to processing
            await self.store.update_batch_status(batch_id, BatchStatus.PROCESSING)

            # Get all resumes
            resumes = await self.store.get_batch_resumes(batch_id, sort_by_score=False)

            if not resumes:
                await self.store.update_batch_status(batch_id, BatchStatus.COMPLETED)
                return {"processed": 0, "failed": 0}

            processed = 0
            failed = 0
            premium_features = batch.get("premium_features", [])
            job_description = batch.get("job_description")

            for resume in resumes:
                try:
                    result = await self._process_single_resume(
                        batch_id,
                        resume,
                        scoring_callback,
                        jd_matching_callback if PremiumFeature.JD_MATCHING.value in premium_features else None,
                        deep_analysis_callback if PremiumFeature.DEEP_ANALYSIS.value in premium_features else None,
                        job_description,
                    )

                    if result.get("success"):
                        processed += 1
                    else:
                        failed += 1

                    # Update progress
                    await self.store.update_batch_status(
                        batch_id,
                        BatchStatus.PROCESSING,
                        processed + failed
                    )

                except Exception as e:
                    print(f"Error processing resume {resume['resume_id']}: {e}")
                    failed += 1

            # Calculate rankings
            await self._calculate_rankings(batch_id)

            # Update final status
            final_status = BatchStatus.COMPLETED if failed == 0 else BatchStatus.COMPLETED
            await self.store.update_batch_status(batch_id, final_status, processed + failed)

            return {
                "processed": processed,
                "failed": failed,
                "total": len(resumes),
            }

        finally:
            self._processing_batches[batch_id] = False

    async def _process_single_resume(
        self,
        batch_id: str,
        resume: Dict[str, Any],
        scoring_callback: Optional[Callable],
        jd_matching_callback: Optional[Callable],
        deep_analysis_callback: Optional[Callable],
        job_description: Optional[str],
    ) -> Dict[str, Any]:
        """Process a single resume."""
        resume_id = resume["resume_id"]

        try:
            # Download and parse resume content
            content = await self.store.get_resume_content(batch_id, resume_id)
            if not content:
                return {"success": False, "error": "Could not download resume"}

            # Parse resume text
            text = self.parser.parse(content, resume["filename"])

            # Extract structured data
            extracted_data = self.extractor.extract(text)
            await self.store.update_resume_extracted_data(batch_id, resume_id, extracted_data)

            # Score resume
            if scoring_callback:
                scores = await scoring_callback(text, extracted_data)
            else:
                scores = self._default_scoring(text, extracted_data)

            overall_score = scores.pop("overall", 0)
            await self.store.update_resume_scores(
                batch_id, resume_id, scores, overall_score
            )

            # JD Matching (if enabled)
            if jd_matching_callback and job_description:
                jd_result = await jd_matching_callback(text, extracted_data, job_description)
                await self.store.update_resume_jd_match(
                    batch_id, resume_id,
                    jd_result.get("match_score", 0),
                    jd_result
                )

            # Deep Analysis (if enabled)
            if deep_analysis_callback:
                analysis = await deep_analysis_callback(text, extracted_data, job_description)
                await self.store.update_resume_deep_analysis(batch_id, resume_id, analysis)

            return {"success": True}

        except Exception as e:
            print(f"Error processing resume {resume_id}: {e}")
            return {"success": False, "error": str(e)}

    def _default_scoring(
        self,
        text: str,
        extracted_data: Dict[str, Any]
    ) -> Dict[str, float]:
        """Default scoring algorithm when no callback provided."""
        scores = {}

        # Skills score (0-100)
        skills = extracted_data.get("skills", [])
        scores["skills"] = min(len(skills) * 10, 100)

        # Experience score (0-100)
        years = extracted_data.get("years_of_experience", 0) or 0
        scores["experience"] = min(years * 10, 100)

        # Education score (0-100)
        education = extracted_data.get("education", [])
        scores["education"] = min(len(education) * 25, 100)

        # Formatting score (based on text structure)
        line_count = len(text.split("\n"))
        word_count = len(text.split())
        scores["formatting"] = min(50 + (line_count * 0.5) + (word_count * 0.01), 100)

        # Overall score (weighted average)
        weights = {
            "skills": 0.35,
            "experience": 0.30,
            "education": 0.20,
            "formatting": 0.15,
        }

        overall = sum(scores.get(k, 0) * w for k, w in weights.items())
        scores["overall"] = round(overall, 2)

        return scores

    async def _calculate_rankings(self, batch_id: str) -> None:
        """Calculate and update rankings for all resumes in batch."""
        resumes = await self.store.get_batch_resumes(batch_id, sort_by_score=True)

        for rank, resume in enumerate(resumes, 1):
            await self.store.update_resume_scores(
                batch_id,
                resume["resume_id"],
                resume.get("scores", {}),
                float(resume.get("overall_score", 0) or 0),
                rank
            )

    async def reprocess_resume(
        self,
        batch_id: str,
        resume_id: str,
        scoring_callback: Optional[Callable] = None,
    ) -> Dict[str, Any]:
        """Reprocess a single resume."""
        resume = await self.store.get_resume(batch_id, resume_id)
        if not resume:
            return {"error": "Resume not found"}

        batch = await self.store.get_batch(batch_id)
        job_description = batch.get("job_description") if batch else None

        result = await self._process_single_resume(
            batch_id, resume, scoring_callback, None, None, job_description
        )

        if result.get("success"):
            await self._calculate_rankings(batch_id)

        return result

    def is_processing(self, batch_id: str) -> bool:
        """Check if a batch is currently being processed."""
        return self._processing_batches.get(batch_id, False)


# Singleton instance
_batch_processor: Optional[BatchProcessor] = None


def get_processor() -> BatchProcessor:
    """Get the batch processor singleton."""
    global _batch_processor
    if _batch_processor is None:
        _batch_processor = BatchProcessor()
    return _batch_processor
