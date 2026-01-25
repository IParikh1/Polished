"""
Pydantic schemas for batch processing in Polished Resume Ranking System.
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
import uuid


class SalesRole(str, Enum):
    """Target sales role for resume optimization."""
    ENTRY_SDR = "entry_sdr"
    SDR = "sdr"
    ACCOUNT_EXECUTIVE = "account_executive"
    SENIOR_AE = "senior_ae"
    ACCOUNT_MANAGER = "account_manager"
    SALES_MANAGER = "sales_manager"


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
    target_role: Optional[SalesRole] = Field(None, description="Target sales role for optimization")

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
    contact_info: Optional[float] = Field(None, ge=0, le=100, description="Contact info completeness score")
    # Tech sales-specific categories (populated when using tech sales scoring)
    achievements: Optional[float] = Field(None, ge=0, le=100, description="Achievements score (quota %, revenue, deals)")
    certifications: Optional[float] = Field(None, ge=0, le=100, description="Certifications score (Salesforce, HubSpot, MEDDIC)")
    career_progression: Optional[float] = Field(None, ge=0, le=100, description="Career progression score (SDR → AE → Senior)")


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


# ==================== JD Matching Schemas (Tech Sales) ====================

class JDMatchRequest(BaseModel):
    """Request to match resume against a job description."""
    session_id: Optional[str] = Field(None, description="Session ID if using session-based flow")
    resume_id: Optional[str] = Field(None, description="Resume ID for batch-based flow")
    batch_id: Optional[str] = Field(None, description="Batch ID for batch-based flow")
    job_description: str = Field(..., min_length=50, description="Full job description text")
    job_url: Optional[str] = Field(None, description="URL of job posting")
    job_title: Optional[str] = Field(None, max_length=200, description="Job title")
    company: Optional[str] = Field(None, max_length=200, description="Company name")
    target_role: Optional[SalesRole] = Field(None, description="Target sales role")

    class Config:
        json_schema_extra = {
            "example": {
                "resume_id": "resume-abc123",
                "batch_id": "batch-xyz789",
                "job_description": "We are looking for an Account Executive with 3+ years of SaaS sales experience...",
                "job_title": "Account Executive",
                "company": "Acme SaaS Inc",
                "target_role": "account_executive"
            }
        }


class JDMatchResult(BaseModel):
    """Result of JD matching analysis."""
    match_score: int = Field(..., ge=0, le=100, description="Overall match score 0-100")
    matching_requirements: List[str] = Field(default_factory=list, description="Requirements that match")
    gaps: List[str] = Field(default_factory=list, description="Missing requirements or gaps")
    keywords_to_add: List[str] = Field(default_factory=list, description="Keywords to add to resume")
    keywords_present: List[str] = Field(default_factory=list, description="Keywords already in resume")
    tailored_suggestions: List[str] = Field(default_factory=list, description="Specific improvement suggestions")
    experience_match: bool = Field(False, description="Whether experience level matches")
    skills_alignment: Optional[Dict[str, bool]] = Field(None, description="Skill-by-skill alignment")


class TailoredResumeRequest(BaseModel):
    """Request to generate a JD-tailored resume."""
    session_id: Optional[str] = Field(None, description="Session ID")
    resume_id: Optional[str] = Field(None, description="Resume ID")
    batch_id: Optional[str] = Field(None, description="Batch ID")
    job_description: str = Field(..., min_length=50, description="Job description to tailor for")
    target_role: Optional[SalesRole] = Field(None, description="Target sales role")
    prioritize_gaps: bool = Field(True, description="Prioritize addressing gaps")
    include_metrics_prompts: bool = Field(True, description="Include prompts for missing metrics")


class TailoredResumeResponse(BaseModel):
    """Response with tailored resume content."""
    tailored_resume: str = Field(..., description="Full tailored resume text")
    changes_made: List[str] = Field(default_factory=list, description="List of changes applied")
    metrics_needed: List[Dict[str, Any]] = Field(default_factory=list, description="Metrics questions to improve resume")
    match_improvement: Optional[int] = Field(None, description="Estimated score improvement")


class SetRoleRequest(BaseModel):
    """Request to set target role for a session/resume."""
    session_id: Optional[str] = Field(None, description="Session ID")
    resume_id: Optional[str] = Field(None, description="Resume ID")
    batch_id: Optional[str] = Field(None, description="Batch ID")
    role: SalesRole = Field(..., description="Target sales role")


class SetRoleResponse(BaseModel):
    """Response confirming role was set."""
    message: str = "Role updated successfully"
    role: SalesRole
    role_display_name: str = Field(..., description="Human-readable role name")


# ==================== Metrics Extraction Schemas ====================

class MetricsQuestion(BaseModel):
    """A question to gather missing metrics from user."""
    company: str = Field(..., description="Company this metric relates to")
    role: str = Field(..., description="Role at that company")
    metric_type: str = Field(..., description="Type of metric (quota, revenue, etc)")
    question: str = Field(..., description="Question to ask user")
    priority: int = Field(1, ge=1, le=5, description="Priority 1-5, 1 being highest")


class MetricsExtractionResult(BaseModel):
    """Result of metrics extraction from resume."""
    metrics_found: Dict[str, str] = Field(default_factory=dict, description="Metrics found in resume")
    metrics_missing: List[MetricsQuestion] = Field(default_factory=list, description="Missing metrics with questions")
    overall_metrics_score: int = Field(..., ge=0, le=100, description="How well resume quantifies achievements")


class MetricsSubmission(BaseModel):
    """User submission of collected metrics."""
    session_id: Optional[str] = None
    resume_id: Optional[str] = None
    batch_id: Optional[str] = None
    metrics: Dict[str, Dict[str, Any]] = Field(..., description="Metrics by company: {company: {metric_type: value}}")


# ==================== Resume Writing Schemas ====================

class ResumeTemplate(str, Enum):
    """Available resume templates."""
    MODERN = "modern"
    CLASSIC = "classic"
    ATS_FRIENDLY = "ats_friendly"
    EXECUTIVE = "executive"
    MINIMAL = "minimal"


class DocumentFormat(str, Enum):
    """Supported document formats."""
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    HTML = "html"


class ExperienceEntry(BaseModel):
    """Experience entry for resume generation."""
    company: str
    title: str
    dates: Optional[str] = None
    location: Optional[str] = None
    bullets: List[str] = Field(default_factory=list)


class EducationEntry(BaseModel):
    """Education entry for resume generation."""
    school: str
    degree: Optional[str] = None
    field: Optional[str] = None
    year: Optional[str] = None
    gpa: Optional[str] = None


class ResumeGenerateRequest(BaseModel):
    """Request to generate an optimized resume."""
    resume_id: Optional[str] = Field(None, description="Resume ID for batch-based flow")
    batch_id: Optional[str] = Field(None, description="Batch ID for batch-based flow")
    session_id: Optional[str] = Field(None, description="Session ID for session-based flow")
    target_role: SalesRole = Field(..., description="Target sales role")
    job_description: Optional[str] = Field(None, description="Optional JD to tailor for")
    metrics: Optional[Dict[str, Dict[str, Any]]] = Field(None, description="Collected metrics by company")
    template: ResumeTemplate = Field(ResumeTemplate.MODERN, description="Resume template style")

    class Config:
        json_schema_extra = {
            "example": {
                "resume_id": "resume-abc123",
                "batch_id": "batch-xyz789",
                "target_role": "account_executive",
                "template": "modern",
                "metrics": {
                    "Acme Corp": {
                        "quota_attainment": "135%",
                        "deals_closed": "45",
                        "avg_deal_size": "$85K"
                    }
                }
            }
        }


class ResumeGenerateResponse(BaseModel):
    """Response with generated resume content."""
    resume_text: str = Field(..., description="Full generated resume text")
    sections: Dict[str, str] = Field(default_factory=dict, description="Resume sections by name")
    changes_made: List[str] = Field(default_factory=list, description="Changes applied from original")
    keywords_added: List[str] = Field(default_factory=list, description="Keywords incorporated")
    suggestions: List[str] = Field(default_factory=list, description="Further improvement suggestions")
    template: ResumeTemplate = Field(ResumeTemplate.MODERN)
    estimated_match_improvement: Optional[int] = Field(None, description="Estimated score improvement if JD provided")


class RewriteSectionRequest(BaseModel):
    """Request to rewrite a specific resume section."""
    resume_id: Optional[str] = None
    batch_id: Optional[str] = None
    session_id: Optional[str] = None
    section_name: str = Field(..., description="Section to rewrite: summary, experience, skills, education")
    section_content: str = Field(..., description="Current section content")
    target_role: SalesRole = Field(..., description="Target sales role")
    context: Optional[str] = Field(None, description="Additional context for rewrite")
    job_description: Optional[str] = Field(None, description="Optional JD for tailoring")


class RewriteSectionResponse(BaseModel):
    """Response with rewritten section."""
    section_name: str
    original: str
    rewritten: str
    changes: List[str] = Field(default_factory=list)
    improvement_score: int = Field(0, ge=0, le=100)


class GenerateSummaryRequest(BaseModel):
    """Request to generate a professional summary."""
    resume_id: Optional[str] = None
    batch_id: Optional[str] = None
    session_id: Optional[str] = None
    target_role: SalesRole = Field(..., description="Target sales role")
    job_description: Optional[str] = Field(None, description="Optional JD for tailoring")
    tone: str = Field("professional", description="Tone: professional, confident, dynamic")


class GenerateSummaryResponse(BaseModel):
    """Response with generated summary variants."""
    standard: str = Field(..., description="Standard professional summary")
    confident: str = Field(..., description="Bold, achievement-focused variant")
    dynamic: str = Field(..., description="Energetic, growth-oriented variant")


class EnhanceBulletsRequest(BaseModel):
    """Request to enhance experience bullet points."""
    resume_id: Optional[str] = None
    batch_id: Optional[str] = None
    bullets: List[str] = Field(..., min_length=1, description="Bullet points to enhance")
    target_role: SalesRole = Field(..., description="Target sales role")
    company_context: Optional[str] = Field(None, description="Context about the company/role")


class EnhancedBullet(BaseModel):
    """Enhanced bullet point result."""
    original: str
    enhanced: str
    needs_metrics: bool = Field(False, description="Whether this bullet needs specific metrics")


class EnhanceBulletsResponse(BaseModel):
    """Response with enhanced bullet points."""
    bullets: List[EnhancedBullet]
    metrics_questions: List[str] = Field(default_factory=list, description="Questions to gather missing metrics")


class ExportResumeRequest(BaseModel):
    """Request to export resume to document format."""
    resume_id: Optional[str] = None
    batch_id: Optional[str] = None
    session_id: Optional[str] = None
    resume_text: Optional[str] = Field(None, description="Generated resume text to export")
    format: DocumentFormat = Field(DocumentFormat.PDF, description="Output format")
    template: ResumeTemplate = Field(ResumeTemplate.MODERN, description="Template style")
    # Structured data for document generation
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin: Optional[str] = None
    summary: Optional[str] = None
    experience: Optional[List[ExperienceEntry]] = None
    education: Optional[List[EducationEntry]] = None
    skills: Optional[List[str]] = None
    certifications: Optional[List[str]] = None


class ExportResumeResponse(BaseModel):
    """Response with exported document."""
    download_url: str = Field(..., description="URL to download the generated document")
    format: DocumentFormat
    filename: str
    expires_at: datetime
    file_size_bytes: Optional[int] = None


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
