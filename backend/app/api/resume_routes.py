"""
Resume Writing API Routes for Polished Tech Sales Resume System.
Premium feature for AI-powered resume generation and document export.
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from typing import Optional
from datetime import datetime, timedelta
import io
import uuid

from ..models.batch_schemas import (
    SalesRole,
    ResumeTemplate,
    DocumentFormat,
    ResumeGenerateRequest,
    ResumeGenerateResponse,
    RewriteSectionRequest,
    RewriteSectionResponse,
    GenerateSummaryRequest,
    GenerateSummaryResponse,
    EnhanceBulletsRequest,
    EnhanceBulletsResponse,
    EnhancedBullet,
    ExportResumeRequest,
    ExportResumeResponse,
)
from ..services.aws_store import get_store
from ..services.resume_writer import get_writer, ResumeTemplate as WriterTemplate
from ..services.document_generator import (
    get_generator,
    DocumentFormat as GenDocFormat,
    ResumeTemplate as GenTemplate,
    ResumeData,
)
from ..services.premium_gate import get_premium_gate, PremiumFeature


router = APIRouter(prefix="/resume", tags=["Resume Writing"])


# ==================== Resume Generation ====================

@router.post("/generate", response_model=ResumeGenerateResponse)
async def generate_resume(request: ResumeGenerateRequest):
    """
    Generate an optimized resume using AI.

    Takes an existing resume and generates an improved version optimized for:
    - Target sales role (SDR, AE, etc.)
    - Specific job description (if provided)
    - Collected metrics from the user

    Premium feature - requires resume_writing access.
    """
    gate = get_premium_gate()
    store = get_store()

    # Check premium access
    if not gate.has_feature("anonymous", PremiumFeature.RESUME_WRITING):
        raise HTTPException(
            status_code=402,
            detail={
                "error": "Resume writing is a premium feature",
                "feature": "resume_writing",
                "upgrade_options": gate.get_upgrade_options("anonymous"),
            }
        )

    # Get resume data
    resume_text = ""
    extracted_data = {}

    if request.batch_id and request.resume_id:
        resume = await store.get_resume(request.batch_id, request.resume_id)
        if not resume:
            raise HTTPException(status_code=404, detail="Resume not found")
        resume_text = resume.get("text", "")
        extracted_data = resume.get("extracted_data", {})
    else:
        raise HTTPException(
            status_code=400,
            detail="Must provide batch_id and resume_id"
        )

    if not resume_text:
        raise HTTPException(status_code=400, detail="Resume text not available")

    # Generate optimized resume
    writer = get_writer()
    result = await writer.generate_resume(
        resume_text=resume_text,
        target_role=request.target_role.value,
        job_description=request.job_description,
        metrics=request.metrics,
        template=WriterTemplate(request.template.value),
        extracted_data=extracted_data,
    )

    # Extract section content
    sections = {}
    for name, section in result.sections.items():
        sections[name] = section.content

    return ResumeGenerateResponse(
        resume_text=result.full_text,
        sections=sections,
        changes_made=result.changes_made,
        keywords_added=result.keywords_added,
        suggestions=result.suggestions,
        template=request.template,
        estimated_match_improvement=result.match_score_improvement,
    )


@router.post("/rewrite-section", response_model=RewriteSectionResponse)
async def rewrite_section(request: RewriteSectionRequest):
    """
    Rewrite a specific section of a resume.

    Supports: summary, experience, skills, education

    Premium feature - requires resume_writing access.
    """
    gate = get_premium_gate()

    # Check premium access
    if not gate.has_feature("anonymous", PremiumFeature.RESUME_WRITING):
        raise HTTPException(
            status_code=402,
            detail={
                "error": "Resume writing is a premium feature",
                "feature": "resume_writing",
                "upgrade_options": gate.get_upgrade_options("anonymous"),
            }
        )

    # Validate section name
    valid_sections = ["summary", "experience", "skills", "education"]
    if request.section_name.lower() not in valid_sections:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid section. Must be one of: {', '.join(valid_sections)}"
        )

    # Rewrite section
    writer = get_writer()
    result = await writer.rewrite_section(
        section_name=request.section_name,
        section_content=request.section_content,
        target_role=request.target_role.value,
        context=request.context,
        job_description=request.job_description,
    )

    return RewriteSectionResponse(
        section_name=result["section"],
        original=result["original"],
        rewritten=result["rewritten"],
        changes=result.get("changes", []),
        improvement_score=result.get("improvement_score", 0),
    )


@router.post("/generate-summary", response_model=GenerateSummaryResponse)
async def generate_summary(request: GenerateSummaryRequest):
    """
    Generate a professional summary for a resume.

    Returns multiple variants:
    - Standard: Professional and balanced
    - Confident: Bold, achievement-focused
    - Dynamic: Energetic, growth-oriented

    Premium feature - requires resume_writing access.
    """
    gate = get_premium_gate()
    store = get_store()

    # Check premium access
    if not gate.has_feature("anonymous", PremiumFeature.RESUME_WRITING):
        raise HTTPException(
            status_code=402,
            detail={
                "error": "Resume writing is a premium feature",
                "feature": "resume_writing",
                "upgrade_options": gate.get_upgrade_options("anonymous"),
            }
        )

    # Get extracted data
    extracted_data = {}
    if request.batch_id and request.resume_id:
        resume = await store.get_resume(request.batch_id, request.resume_id)
        if resume:
            extracted_data = resume.get("extracted_data", {})

    # Generate summaries
    writer = get_writer()
    summaries = await writer.generate_summary(
        extracted_data=extracted_data,
        target_role=request.target_role.value,
        job_description=request.job_description,
        tone=request.tone,
    )

    return GenerateSummaryResponse(
        standard=summaries.get("standard", ""),
        confident=summaries.get("confident", ""),
        dynamic=summaries.get("dynamic", ""),
    )


@router.post("/enhance-bullets", response_model=EnhanceBulletsResponse)
async def enhance_bullets(request: EnhanceBulletsRequest):
    """
    Enhance experience bullet points with metrics and impact.

    Takes basic bullet points and transforms them into:
    - Achievement-focused statements
    - Metrics-first format
    - Action verb openers

    Premium feature - requires resume_writing access.
    """
    gate = get_premium_gate()

    # Check premium access
    if not gate.has_feature("anonymous", PremiumFeature.RESUME_WRITING):
        raise HTTPException(
            status_code=402,
            detail={
                "error": "Resume writing is a premium feature",
                "feature": "resume_writing",
                "upgrade_options": gate.get_upgrade_options("anonymous"),
            }
        )

    # Enhance bullets
    writer = get_writer()
    enhanced = await writer.enhance_bullets(
        bullets=request.bullets,
        target_role=request.target_role.value,
        company_context=request.company_context,
    )

    # Extract metrics questions from bullets that need them
    metrics_questions = []
    for bullet in enhanced:
        if bullet.get("needs_metrics"):
            metrics_questions.append(
                f"What specific numbers can you provide for: {bullet.get('original', '')[:50]}...?"
            )

    return EnhanceBulletsResponse(
        bullets=[
            EnhancedBullet(
                original=b.get("original", ""),
                enhanced=b.get("enhanced", ""),
                needs_metrics=b.get("needs_metrics", False),
            )
            for b in enhanced
        ],
        metrics_questions=metrics_questions[:5],
    )


# ==================== Document Export ====================

@router.post("/export", response_model=ExportResumeResponse)
async def export_resume(request: ExportResumeRequest):
    """
    Export resume to a formatted document (PDF, DOCX, TXT, HTML).

    Takes either:
    - Generated resume text from /generate endpoint
    - Structured resume data with sections

    Premium feature - requires resume_writing access.
    """
    gate = get_premium_gate()
    store = get_store()

    # Check premium access
    if not gate.has_feature("anonymous", PremiumFeature.RESUME_WRITING):
        raise HTTPException(
            status_code=402,
            detail={
                "error": "Resume export is a premium feature",
                "feature": "resume_writing",
                "upgrade_options": gate.get_upgrade_options("anonymous"),
            }
        )

    # Build resume data
    resume_data = {}

    # If resume_id provided, get extracted data
    if request.batch_id and request.resume_id:
        resume = await store.get_resume(request.batch_id, request.resume_id)
        if resume:
            extracted = resume.get("extracted_data", {})
            resume_data = {
                "name": extracted.get("name", ""),
                "email": extracted.get("email"),
                "phone": extracted.get("phone"),
                "summary": extracted.get("summary"),
                "skills": extracted.get("skills", []),
            }

    # Override with explicit request data
    if request.name:
        resume_data["name"] = request.name
    if request.email:
        resume_data["email"] = request.email
    if request.phone:
        resume_data["phone"] = request.phone
    if request.location:
        resume_data["location"] = request.location
    if request.linkedin:
        resume_data["linkedin"] = request.linkedin
    if request.summary:
        resume_data["summary"] = request.summary
    if request.skills:
        resume_data["skills"] = request.skills
    if request.certifications:
        resume_data["certifications"] = request.certifications

    # Convert experience entries
    if request.experience:
        resume_data["experience"] = [
            {
                "company": exp.company,
                "title": exp.title,
                "dates": exp.dates,
                "location": exp.location,
                "bullets": exp.bullets,
            }
            for exp in request.experience
        ]

    # Convert education entries
    if request.education:
        resume_data["education"] = [
            {
                "school": edu.school,
                "degree": edu.degree,
                "field": edu.field,
                "year": edu.year,
                "gpa": edu.gpa,
            }
            for edu in request.education
        ]

    # Ensure we have minimum required data
    if not resume_data.get("name"):
        resume_data["name"] = "Candidate"

    # Generate document
    generator = get_generator()
    try:
        doc_bytes = generator.generate(
            resume_data=resume_data,
            format=GenDocFormat(request.format.value),
            template=GenTemplate(request.template.value),
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate document: {str(e)}"
        )

    # Create export in S3
    export_id = f"export-{uuid.uuid4().hex[:12]}"
    filename = f"{resume_data.get('name', 'resume').replace(' ', '_')}_{export_id}.{request.format.value}"

    # For now, we'll return a data URL for direct download
    # In production, this would upload to S3 and return a presigned URL
    export = await store.create_export(
        batch_id=request.batch_id or "standalone",
        content=doc_bytes,
        format_type=request.format.value,
    )

    if not export:
        raise HTTPException(status_code=500, detail="Failed to create export")

    return ExportResumeResponse(
        download_url=export["download_url"],
        format=request.format,
        filename=filename,
        expires_at=datetime.utcnow() + timedelta(hours=1),
        file_size_bytes=len(doc_bytes),
    )


@router.get("/export/{export_id}/download")
async def download_export(export_id: str, format: DocumentFormat = DocumentFormat.PDF):
    """
    Download a previously generated document export.

    Returns the document file directly.
    """
    # This endpoint would retrieve the document from S3
    # For now, returns a placeholder
    raise HTTPException(
        status_code=404,
        detail="Export not found or expired"
    )


# ==================== Templates & Configuration ====================

@router.get("/templates")
async def list_templates():
    """
    List available resume templates with descriptions.
    """
    return {
        "templates": [
            {
                "id": "modern",
                "name": "Modern",
                "description": "Clean, contemporary design with accent colors. Good for tech sales roles.",
                "recommended_for": ["sdr", "account_executive", "senior_ae"],
            },
            {
                "id": "classic",
                "name": "Classic",
                "description": "Traditional format with centered header. Professional and timeless.",
                "recommended_for": ["sales_manager", "account_manager"],
            },
            {
                "id": "ats_friendly",
                "name": "ATS-Friendly",
                "description": "Optimized for Applicant Tracking Systems. Simple formatting, no graphics.",
                "recommended_for": ["entry_sdr", "sdr", "account_executive"],
            },
            {
                "id": "executive",
                "name": "Executive",
                "description": "Sophisticated design for senior roles. Emphasis on leadership and strategy.",
                "recommended_for": ["senior_ae", "sales_manager"],
            },
            {
                "id": "minimal",
                "name": "Minimal",
                "description": "Clean and simple. Focuses on content with minimal styling.",
                "recommended_for": ["entry_sdr", "sdr"],
            },
        ]
    }


@router.get("/roles")
async def list_roles():
    """
    List available target sales roles with descriptions.
    """
    from ..services.resume_agent import ROLE_CONFIGS

    return {
        "roles": [
            {
                "id": role_id,
                "name": config.display_name,
                "experience_range": f"{config.experience_range[0]}-{config.experience_range[1]} years",
                "key_metrics": config.metrics_keywords[:5],
            }
            for role_id, config in ROLE_CONFIGS.items()
        ]
    }


@router.get("/writing-status")
async def get_writing_status():
    """
    Check if resume writing service is available.

    Returns service status and capabilities.
    """
    writer = get_writer()

    return {
        "available": writer.is_available(),
        "llm_enabled": writer.is_available(),
        "supported_formats": ["pdf", "docx", "txt", "html"],
        "supported_templates": ["modern", "classic", "ats_friendly", "executive", "minimal"],
        "features": {
            "full_resume_generation": writer.is_available(),
            "section_rewriting": True,
            "summary_generation": True,
            "bullet_enhancement": True,
            "document_export": True,
            "metrics_extraction": True,
        }
    }


# ==================== Metrics Extraction ====================

@router.post("/extract-metrics")
async def extract_metrics(
    batch_id: Optional[str] = None,
    resume_id: Optional[str] = None,
    target_role: SalesRole = SalesRole.ACCOUNT_EXECUTIVE,
):
    """
    Extract sales metrics from a resume and identify what's missing.

    Returns found metrics, missing metrics with questions, and an overall score.
    """
    from ..services.metrics_extractor import get_extractor

    store = get_store()
    extractor = get_extractor()

    # Get resume text
    resume_text = ""
    extracted_data = {}

    if batch_id and resume_id:
        resume = await store.get_resume(batch_id, resume_id)
        if not resume:
            raise HTTPException(status_code=404, detail="Resume not found")
        resume_text = resume.get("text", "")
        extracted_data = resume.get("extracted_data", {})
    else:
        raise HTTPException(
            status_code=400,
            detail="Must provide batch_id and resume_id"
        )

    if not resume_text:
        raise HTTPException(status_code=400, detail="Resume text not available")

    # Extract metrics
    result = extractor.extract_metrics(
        resume_text=resume_text,
        target_role=target_role.value,
        extracted_data=extracted_data,
    )

    return {
        "metrics_found": [
            {
                "metric_type": m.metric_type,
                "value": m.value,
                "context": m.context,
            }
            for m in result.metrics_found
        ],
        "metrics_missing": [
            {
                "metric_type": m.metric_type,
                "question": m.question,
                "company": m.company,
                "role": m.role,
                "priority": m.priority,
            }
            for m in result.metrics_missing
        ],
        "overall_score": result.overall_score,
        "recommendations": result.recommendations,
    }


@router.post("/format-metrics")
async def format_metrics(
    metrics: dict,
    target_role: SalesRole = SalesRole.ACCOUNT_EXECUTIVE,
):
    """
    Format collected metrics into resume-ready bullet points.

    Takes: {company: {metric_type: value}}
    Returns: {company: formatted_bullets}
    """
    from ..services.metrics_extractor import get_extractor

    extractor = get_extractor()
    formatted = extractor.format_metrics_for_resume(
        metrics=metrics,
        target_role=target_role.value,
    )

    return {"formatted_metrics": formatted}
