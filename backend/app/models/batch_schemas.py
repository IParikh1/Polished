"""
Pydantic schemas for batch processing in Polished Resume Ranking System.
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
import uuid


class BatchStatus(str, Enum):
    """Batch processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ResumeStatus(str, Enum):
    """Individual resume processing status."""
    PENDING = "pending"
    UPLOADING = "uploading"
    PROCESSING = "processing"
    SCORED = "scored"
    FAILED = "failed"


class PremiumFeature(str, Enum):
    """Available premium features."""
    JD_MATCHING = "jd_matching"
    DEEP_ANALYSIS = "deep_analysis"
    CONSULTING = "consulting"


class PlacementStatus(str, Enum):
    """Placement verification status."""
    PENDING = "pending"
    VERIFIED = "verified"
    DISPUTED = "disputed"
    REJECTED = "rejected"


# ==================== Request Schemas ====================

class BatchCreateRequest(BaseModel):
    """Request to create a new batch."""
    name: Optional[str] = Field(None, max_length=200, description="Batch name")
    job_description: Optional[str] = Field(None, description="Job description for matching")
    premium_features: List[PremiumFeature] = Field(default_factory=list, description="Enabled premium features")
    settings: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Batch settings")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Software Engineers Q1 2026",
                "job_description": "Looking for senior Python developers...",
                "premium_features": ["jd_matching"],
                "settings": {"min_score_threshold": 60}
            }
        }


class ResumeUploadRequest(BaseModel):
    """Request to upload a resume to a batch."""
    filename: str = Field(..., min_length=1, max_length=500, description="Original filename")
    content_type: Optional[str] = Field(None, description="MIME type")

    @validator("filename")
    def validate_filename(cls, v):
        allowed_extensions = [".pdf", ".doc", ".docx", ".txt", ".rtf"]
        ext = v.lower().split(".")[-1] if "." in v else ""
        if f".{ext}" not in allowed_extensions:
            raise ValueError(f"File type .{ext} not supported. Use: {allowed_extensions}")
        return v


class BatchUploadRequest(BaseModel):
    """Request for batch upload initiation."""
    batch_id: str = Field(..., description="Batch ID to upload to")
    files: List[ResumeUploadRequest] = Field(..., min_items=1, max_items=1000, description="Files to upload")


class BatchUpdateRequest(BaseModel):
    """Request to update batch settings."""
    name: Optional[str] = Field(None, max_length=200)
    job_description: Optional[str] = None
    premium_features: Optional[List[PremiumFeature]] = None
    settings: Optional[Dict[str, Any]] = None


class ScoreFilterRequest(BaseModel):
    """Request to filter scored resumes."""
    min_score: Optional[float] = Field(None, ge=0, le=100, description="Minimum overall score")
    max_score: Optional[float] = Field(None, ge=0, le=100, description="Maximum overall score")
    min_jd_match: Optional[float] = Field(None, ge=0, le=100, description="Minimum JD match score")
    skills: Optional[List[str]] = Field(None, description="Required skills filter")
    experience_years: Optional[int] = Field(None, ge=0, description="Minimum years of experience")
    sort_by: Optional[str] = Field("overall_score", description="Sort field")
    sort_order: Optional[str] = Field("desc", description="Sort order (asc/desc)")
    limit: Optional[int] = Field(50, ge=1, le=500, description="Result limit")
    offset: Optional[int] = Field(0, ge=0, description="Pagination offset")


class ExportRequest(BaseModel):
    """Request to export batch results."""
    format: str = Field("json", description="Export format (json/csv)")
    include_scores: bool = Field(True, description="Include scoring details")
    include_extracted_data: bool = Field(False, description="Include parsed resume data")
    include_jd_match: bool = Field(False, description="Include JD matching details")
    include_deep_analysis: bool = Field(False, description="Include deep analysis (premium)")
    filters: Optional[ScoreFilterRequest] = None

    @validator("format")
    def validate_format(cls, v):
        if v.lower() not in ["json", "csv"]:
            raise ValueError("Format must be 'json' or 'csv'")
        return v.lower()


class PlacementCreateRequest(BaseModel):
    """Request to report a placement."""
    batch_id: str = Field(..., description="Source batch ID")
    resume_id: str = Field(..., description="Placed resume ID")
    company_name: str = Field(..., min_length=1, max_length=200, description="Hiring company")
    position: str = Field(..., min_length=1, max_length=200, description="Job title")
    candidate_name: Optional[str] = Field(None, max_length=200, description="Candidate name")
    placement_date: Optional[datetime] = Field(None, description="Date of placement")
    notes: Optional[str] = Field(None, max_length=2000, description="Additional notes")

    class Config:
        json_schema_extra = {
            "example": {
                "batch_id": "batch-123",
                "resume_id": "resume-456",
                "company_name": "Acme Corp",
                "position": "Senior Software Engineer",
                "candidate_name": "John Doe",
                "placement_date": "2026-01-15T00:00:00Z",
                "notes": "Started immediately"
            }
        }


class PlacementVerifyRequest(BaseModel):
    """Request to verify a placement."""
    verification_method: str = Field(..., description="How placement was verified")
    verification_details: Optional[Dict[str, Any]] = Field(None, description="Verification evidence")
    verified: bool = Field(..., description="Whether placement is verified")


# ==================== Response Schemas ====================

class ScoreBreakdown(BaseModel):
    """Detailed score breakdown for a resume."""
    overall: float = Field(..., ge=0, le=100, description="Overall score")
    experience: Optional[float] = Field(None, ge=0, le=100, description="Experience score")
    skills: Optional[float] = Field(None, ge=0, le=100, description="Skills score")
    education: Optional[float] = Field(None, ge=0, le=100, description="Education score")
    formatting: Optional[float] = Field(None, ge=0, le=100, description="Formatting score")
    keywords: Optional[float] = Field(None, ge=0, le=100, description="Keywords score")


class ExtractedResumeData(BaseModel):
    """Data extracted from a resume."""
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    summary: Optional[str] = None
    skills: Optional[List[str]] = None
    experience: Optional[List[Dict[str, Any]]] = None
    education: Optional[List[Dict[str, Any]]] = None
    certifications: Optional[List[str]] = None
    languages: Optional[List[str]] = None
    years_of_experience: Optional[int] = None


class JDMatchDetails(BaseModel):
    """JD matching details (premium feature)."""
    match_score: float = Field(..., ge=0, le=100)
    matched_skills: List[str] = Field(default_factory=list)
    missing_skills: List[str] = Field(default_factory=list)
    experience_match: bool = Field(False)
    education_match: bool = Field(False)
    keyword_matches: List[str] = Field(default_factory=list)
    recommendation: Optional[str] = None


class DeepAnalysis(BaseModel):
    """Deep LLM analysis results (premium feature)."""
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    culture_fit_score: Optional[float] = Field(None, ge=0, le=100)
    growth_potential: Optional[str] = None
    red_flags: List[str] = Field(default_factory=list)
    interview_questions: List[str] = Field(default_factory=list)
    overall_assessment: Optional[str] = None


class ResumeResponse(BaseModel):
    """Response containing resume data."""
    resume_id: str
    batch_id: str
    filename: str
    status: ResumeStatus
    created_at: datetime
    updated_at: datetime
    rank: Optional[int] = None
    scores: Optional[ScoreBreakdown] = None
    extracted_data: Optional[ExtractedResumeData] = None
    jd_match: Optional[JDMatchDetails] = None
    deep_analysis: Optional[DeepAnalysis] = None
    download_url: Optional[str] = None


class BatchResponse(BaseModel):
    """Response containing batch data."""
    batch_id: str
    name: str
    status: BatchStatus
    total_resumes: int
    processed_resumes: int
    created_at: datetime
    updated_at: datetime
    job_description: Optional[str] = None
    premium_features: List[PremiumFeature] = Field(default_factory=list)
    settings: Dict[str, Any] = Field(default_factory=dict)
    progress_percent: float = Field(0, ge=0, le=100)

    @validator("progress_percent", always=True)
    def calculate_progress(cls, v, values):
        total = values.get("total_resumes", 0)
        processed = values.get("processed_resumes", 0)
        if total > 0:
            return round((processed / total) * 100, 1)
        return 0


class BatchListResponse(BaseModel):
    """Response containing list of batches."""
    batches: List[BatchResponse]
    total: int
    limit: int
    offset: int


class RankingResponse(BaseModel):
    """Response containing ranked resumes."""
    batch_id: str
    resumes: List[ResumeResponse]
    total: int
    filters_applied: Optional[ScoreFilterRequest] = None


class UploadUrlResponse(BaseModel):
    """Response with presigned upload URL."""
    resume_id: str
    upload_url: str
    s3_key: str
    content_type: str
    expires_in: int = 3600


class BatchUploadResponse(BaseModel):
    """Response for batch upload initiation."""
    batch_id: str
    upload_urls: List[UploadUrlResponse]


class ExportResponse(BaseModel):
    """Response with export download URL."""
    export_id: str
    batch_id: str
    format: str
    download_url: str
    created_at: datetime
    expires_at: datetime
    record_count: int


class PlacementResponse(BaseModel):
    """Response containing placement data."""
    placement_id: str
    batch_id: str
    resume_id: str
    company_name: str
    position: str
    candidate_name: Optional[str] = None
    placement_date: datetime
    reported_at: datetime
    verification_status: PlacementStatus
    fee_amount: float = 250.00
    fee_paid: bool = False
    verification_details: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None


class PlacementListResponse(BaseModel):
    """Response containing list of placements."""
    placements: List[PlacementResponse]
    total: int
    stats: Optional[Dict[str, Any]] = None


class PlacementStatsResponse(BaseModel):
    """Response with placement statistics."""
    total_placements: int
    verified: int
    pending: int
    disputed: int
    total_revenue: float
    pending_revenue: float


# ==================== Error Schemas ====================

class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None


class ValidationErrorResponse(BaseModel):
    """Validation error response."""
    error: str = "Validation Error"
    details: List[Dict[str, Any]]


# ==================== Utility Functions ====================

def generate_batch_id() -> str:
    """Generate a unique batch ID."""
    return f"batch-{uuid.uuid4().hex[:12]}"


def generate_resume_id() -> str:
    """Generate a unique resume ID."""
    return f"resume-{uuid.uuid4().hex[:12]}"


def generate_placement_id() -> str:
    """Generate a unique placement ID."""
    return f"placement-{uuid.uuid4().hex[:12]}"


def generate_export_id() -> str:
    """Generate a unique export ID."""
    return f"export-{uuid.uuid4().hex[:12]}"
