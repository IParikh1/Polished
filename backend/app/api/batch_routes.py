"""
Batch API Routes for Polished Resume Ranking System.
Handles batch creation, resume upload, scoring, and export.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Query, BackgroundTasks
from fastapi.responses import JSONResponse, StreamingResponse
from typing import List, Optional
from datetime import datetime, timedelta
import csv
import io
import json

from ..models.batch_schemas import (
    BatchCreateRequest,
    BatchUpdateRequest,
    BatchResponse,
    BatchListResponse,
    ResumeResponse,
    RankingResponse,
    UploadUrlResponse,
    BatchUploadResponse,
    ExportRequest,
    ExportResponse,
    ScoreFilterRequest,
    BatchStatus,
    ResumeStatus,
    generate_batch_id,
    generate_resume_id,
    generate_export_id,
)
from ..services.aws_store import get_store
from ..services.batch_processor import get_processor
from ..services.batch_cache import get_cache
from ..services.premium_gate import get_premium_gate, PremiumFeature


router = APIRouter(prefix="/batches", tags=["Batches"])


# ==================== Batch CRUD Operations ====================

@router.post("", response_model=BatchResponse)
async def create_batch(request: BatchCreateRequest):
    """
    Create a new batch for resume processing.

    - **name**: Optional batch name
    - **job_description**: Optional JD for matching (premium)
    - **premium_features**: List of enabled premium features
    - **settings**: Custom batch settings
    """
    store = get_store()
    gate = get_premium_gate()

    # Validate premium features
    if request.premium_features:
        validation = gate.validate_batch_features(
            "anonymous",  # Replace with actual user_id when auth is added
            [f.value for f in request.premium_features]
        )
        if not validation["valid"]:
            raise HTTPException(
                status_code=402,
                detail={
                    "error": "Premium features not available",
                    "denied_features": validation["denied_features"],
                    "upgrade_options": gate.get_upgrade_options("anonymous")
                }
            )

    batch = await store.create_batch(
        name=request.name,
        job_description=request.job_description,
        premium_features=[f.value for f in request.premium_features] if request.premium_features else [],
        settings=request.settings,
    )

    # Cache the batch
    cache = get_cache()
    cache.cache_batch(batch["batch_id"], batch)

    return BatchResponse(
        batch_id=batch["batch_id"],
        name=batch["name"],
        status=BatchStatus(batch["status"]),
        total_resumes=batch["total_resumes"],
        processed_resumes=batch["processed_resumes"],
        created_at=datetime.fromisoformat(batch["created_at"]),
        updated_at=datetime.fromisoformat(batch["updated_at"]),
        job_description=batch.get("job_description"),
        premium_features=batch.get("premium_features", []),
        settings=batch.get("settings", {}),
    )


@router.get("", response_model=BatchListResponse)
async def list_batches(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """List all batches with pagination."""
    store = get_store()
    batches = await store.list_batches(limit=limit)

    batch_responses = [
        BatchResponse(
            batch_id=b["batch_id"],
            name=b["name"],
            status=BatchStatus(b["status"]),
            total_resumes=b.get("total_resumes", 0),
            processed_resumes=b.get("processed_resumes", 0),
            created_at=datetime.fromisoformat(b["created_at"]),
            updated_at=datetime.fromisoformat(b["updated_at"]),
            job_description=b.get("job_description"),
            premium_features=b.get("premium_features", []),
            settings=b.get("settings", {}),
        )
        for b in batches[offset:offset + limit]
    ]

    return BatchListResponse(
        batches=batch_responses,
        total=len(batches),
        limit=limit,
        offset=offset,
    )


@router.get("/{batch_id}", response_model=BatchResponse)
async def get_batch(batch_id: str):
    """Get batch by ID."""
    # Check cache first
    cache = get_cache()
    cached = cache.get_cached_batch(batch_id)

    if cached:
        return BatchResponse(
            batch_id=cached["batch_id"],
            name=cached["name"],
            status=BatchStatus(cached["status"]),
            total_resumes=cached.get("total_resumes", 0),
            processed_resumes=cached.get("processed_resumes", 0),
            created_at=datetime.fromisoformat(cached["created_at"]),
            updated_at=datetime.fromisoformat(cached["updated_at"]),
            job_description=cached.get("job_description"),
            premium_features=cached.get("premium_features", []),
            settings=cached.get("settings", {}),
        )

    store = get_store()
    batch = await store.get_batch(batch_id)

    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    # Cache for next time
    cache.cache_batch(batch_id, batch)

    return BatchResponse(
        batch_id=batch["batch_id"],
        name=batch["name"],
        status=BatchStatus(batch["status"]),
        total_resumes=batch.get("total_resumes", 0),
        processed_resumes=batch.get("processed_resumes", 0),
        created_at=datetime.fromisoformat(batch["created_at"]),
        updated_at=datetime.fromisoformat(batch["updated_at"]),
        job_description=batch.get("job_description"),
        premium_features=batch.get("premium_features", []),
        settings=batch.get("settings", {}),
    )


@router.patch("/{batch_id}", response_model=BatchResponse)
async def update_batch(batch_id: str, request: BatchUpdateRequest):
    """Update batch settings."""
    store = get_store()
    cache = get_cache()

    batch = await store.get_batch(batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    # Build updates
    updates = {}
    if request.name is not None:
        updates["name"] = request.name
    if request.job_description is not None:
        updates["job_description"] = request.job_description
    if request.premium_features is not None:
        updates["premium_features"] = [f.value for f in request.premium_features]
    if request.settings is not None:
        updates["settings"] = request.settings

    updated = await store.update_batch(batch_id, **updates)

    # Invalidate cache
    cache.invalidate_batch(batch_id)

    return BatchResponse(
        batch_id=updated["batch_id"],
        name=updated["name"],
        status=BatchStatus(updated["status"]),
        total_resumes=updated.get("total_resumes", 0),
        processed_resumes=updated.get("processed_resumes", 0),
        created_at=datetime.fromisoformat(updated["created_at"]),
        updated_at=datetime.fromisoformat(updated["updated_at"]),
        job_description=updated.get("job_description"),
        premium_features=updated.get("premium_features", []),
        settings=updated.get("settings", {}),
    )


@router.delete("/{batch_id}")
async def delete_batch(batch_id: str):
    """Delete a batch and all associated data."""
    store = get_store()
    cache = get_cache()

    batch = await store.get_batch(batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    success = await store.delete_batch(batch_id)

    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete batch")

    # Invalidate cache
    cache.invalidate_batch(batch_id)

    return {"message": "Batch deleted successfully"}


# ==================== Resume Upload Operations ====================

@router.post("/{batch_id}/upload-urls", response_model=BatchUploadResponse)
async def get_upload_urls(
    batch_id: str,
    filenames: List[str] = Query(..., description="List of filenames to upload"),
):
    """
    Get presigned URLs for direct upload to S3.

    Returns upload URLs for each file that can be used for direct PUT requests.
    """
    store = get_store()

    batch = await store.get_batch(batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    upload_urls = []
    for filename in filenames:
        resume_id = generate_resume_id()

        # Create resume record
        await store.add_resume(batch_id, filename)

        # Get upload URL
        url_info = await store.get_resume_upload_url(batch_id, resume_id, filename)

        if url_info:
            upload_urls.append(UploadUrlResponse(
                resume_id=resume_id,
                upload_url=url_info["url"],
                s3_key=url_info["s3_key"],
                content_type=url_info["content_type"],
            ))

    return BatchUploadResponse(
        batch_id=batch_id,
        upload_urls=upload_urls,
    )


@router.post("/{batch_id}/upload")
async def upload_resume(
    batch_id: str,
    file: UploadFile = File(...),
):
    """
    Upload a single resume file directly.

    Supports: PDF, DOCX, DOC, TXT, RTF
    """
    store = get_store()

    batch = await store.get_batch(batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    # Validate file type
    allowed_types = [".pdf", ".doc", ".docx", ".txt", ".rtf"]
    ext = "." + file.filename.lower().split(".")[-1] if "." in file.filename else ""
    if ext not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"File type {ext} not supported. Allowed: {allowed_types}"
        )

    # Read file content
    content = await file.read()

    # Add resume
    resume = await store.add_resume(
        batch_id,
        file.filename,
        file_content=content,
        content_type=file.content_type,
    )

    return {
        "resume_id": resume["resume_id"],
        "filename": resume["filename"],
        "status": resume["status"],
    }


@router.post("/{batch_id}/upload-multiple")
async def upload_multiple_resumes(
    batch_id: str,
    files: List[UploadFile] = File(...),
):
    """Upload multiple resume files at once."""
    store = get_store()

    batch = await store.get_batch(batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    results = []
    allowed_types = [".pdf", ".doc", ".docx", ".txt", ".rtf"]

    for file in files:
        ext = "." + file.filename.lower().split(".")[-1] if "." in file.filename else ""

        if ext not in allowed_types:
            results.append({
                "filename": file.filename,
                "status": "error",
                "error": f"File type {ext} not supported"
            })
            continue

        try:
            content = await file.read()
            resume = await store.add_resume(
                batch_id,
                file.filename,
                file_content=content,
                content_type=file.content_type,
            )
            results.append({
                "resume_id": resume["resume_id"],
                "filename": resume["filename"],
                "status": "uploaded",
            })
        except Exception as e:
            results.append({
                "filename": file.filename,
                "status": "error",
                "error": str(e)
            })

    return {
        "batch_id": batch_id,
        "uploaded": len([r for r in results if r["status"] == "uploaded"]),
        "failed": len([r for r in results if r["status"] == "error"]),
        "results": results,
    }


@router.post("/{batch_id}/resumes/{resume_id}/confirm-upload")
async def confirm_resume_upload(
    batch_id: str,
    resume_id: str,
    s3_key: str = Query(..., description="S3 key of uploaded file"),
):
    """Confirm that a resume was uploaded successfully via presigned URL."""
    store = get_store()

    success = await store.confirm_resume_upload(batch_id, resume_id, s3_key)

    if not success:
        raise HTTPException(status_code=404, detail="Resume not found")

    return {"message": "Upload confirmed", "resume_id": resume_id}


# ==================== Processing Operations ====================

@router.post("/{batch_id}/process")
async def process_batch(batch_id: str, background_tasks: BackgroundTasks):
    """
    Start processing all resumes in a batch.

    This runs in the background and updates batch status.
    """
    store = get_store()
    processor = get_processor()
    cache = get_cache()

    batch = await store.get_batch(batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    if processor.is_processing(batch_id):
        raise HTTPException(status_code=409, detail="Batch is already being processed")

    # Start processing in background
    background_tasks.add_task(processor.process_batch, batch_id)

    # Set processing status in cache
    cache.set_processing_status(batch_id, "processing", {"started_at": datetime.utcnow().isoformat()})

    return {
        "message": "Processing started",
        "batch_id": batch_id,
        "status": "processing",
    }


@router.get("/{batch_id}/processing-status")
async def get_processing_status(batch_id: str):
    """Get the current processing status of a batch."""
    cache = get_cache()
    store = get_store()

    # Check cache for real-time status
    cached_status = cache.get_processing_status(batch_id)

    # Get batch from store
    batch = await store.get_batch(batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    return {
        "batch_id": batch_id,
        "status": batch["status"],
        "total_resumes": batch.get("total_resumes", 0),
        "processed_resumes": batch.get("processed_resumes", 0),
        "progress_percent": (
            (batch.get("processed_resumes", 0) / batch.get("total_resumes", 1)) * 100
            if batch.get("total_resumes", 0) > 0 else 0
        ),
        "processing_details": cached_status,
    }


# ==================== Resume and Ranking Operations ====================

@router.get("/{batch_id}/resumes")
async def get_batch_resumes(
    batch_id: str,
    include_download_urls: bool = Query(False),
):
    """Get all resumes in a batch."""
    store = get_store()

    batch = await store.get_batch(batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    resumes = await store.get_batch_resumes(
        batch_id,
        sort_by_score=True,
        include_download_urls=include_download_urls,
    )

    return {
        "batch_id": batch_id,
        "total": len(resumes),
        "resumes": resumes,
    }


@router.get("/{batch_id}/resumes/{resume_id}")
async def get_resume(
    batch_id: str,
    resume_id: str,
    include_download_url: bool = Query(True),
):
    """Get a specific resume with all its data."""
    store = get_store()

    resume = await store.get_resume(
        batch_id,
        resume_id,
        include_download_url=include_download_url,
    )

    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    return resume


@router.get("/{batch_id}/rankings", response_model=RankingResponse)
async def get_rankings(
    batch_id: str,
    min_score: Optional[float] = Query(None, ge=0, le=100),
    max_score: Optional[float] = Query(None, ge=0, le=100),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """
    Get ranked resumes with optional filtering.

    Returns resumes sorted by overall score in descending order.
    """
    store = get_store()
    cache = get_cache()

    batch = await store.get_batch(batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    # Create filter hash for caching
    filters = ScoreFilterRequest(
        min_score=min_score,
        max_score=max_score,
        limit=limit,
        offset=offset,
    )
    filter_hash = cache.generate_filter_hash(filters.model_dump())

    # Check cache
    cached = cache.get_cached_rankings(batch_id, filter_hash)
    if cached:
        return RankingResponse(
            batch_id=batch_id,
            resumes=[ResumeResponse(**r) for r in cached],
            total=len(cached),
            filters_applied=filters,
        )

    # Get from store
    resumes = await store.get_batch_resumes(batch_id, sort_by_score=True)

    # Apply filters
    if min_score is not None:
        resumes = [r for r in resumes if (r.get("overall_score") or 0) >= min_score]
    if max_score is not None:
        resumes = [r for r in resumes if (r.get("overall_score") or 0) <= max_score]

    # Apply pagination
    total = len(resumes)
    resumes = resumes[offset:offset + limit]

    # Convert to response format
    resume_responses = []
    for r in resumes:
        resume_responses.append(ResumeResponse(
            resume_id=r["resume_id"],
            batch_id=r["batch_id"],
            filename=r["filename"],
            status=ResumeStatus(r.get("status", "pending")),
            created_at=datetime.fromisoformat(r["created_at"]),
            updated_at=datetime.fromisoformat(r["updated_at"]),
            rank=r.get("rank"),
            scores=r.get("scores"),
            extracted_data=r.get("extracted_data"),
            jd_match=r.get("jd_match_details"),
            deep_analysis=r.get("deep_analysis"),
        ))

    # Cache results
    cache.cache_rankings(batch_id, [r.model_dump() for r in resume_responses], filter_hash)

    return RankingResponse(
        batch_id=batch_id,
        resumes=resume_responses,
        total=total,
        filters_applied=filters,
    )


# ==================== Export Operations ====================

@router.post("/{batch_id}/export", response_model=ExportResponse)
async def export_batch(batch_id: str, request: ExportRequest):
    """
    Export batch results to CSV or JSON.

    Returns a download URL for the export file.
    """
    store = get_store()
    gate = get_premium_gate()

    batch = await store.get_batch(batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    # Check premium features if exporting premium data
    if request.include_deep_analysis and not gate.has_feature("anonymous", PremiumFeature.DEEP_ANALYSIS):
        raise HTTPException(status_code=402, detail="Deep analysis export requires premium subscription")

    # Get resumes
    resumes = await store.get_batch_resumes(batch_id, sort_by_score=True)

    # Build export data
    export_data = []
    for resume in resumes:
        record = {
            "resume_id": resume["resume_id"],
            "filename": resume["filename"],
            "rank": resume.get("rank"),
            "status": resume.get("status"),
        }

        if request.include_scores:
            record["overall_score"] = resume.get("overall_score")
            record["scores"] = resume.get("scores", {})

        if request.include_extracted_data:
            record["extracted_data"] = resume.get("extracted_data", {})

        if request.include_jd_match:
            record["jd_match_score"] = resume.get("jd_match_score")
            record["jd_match_details"] = resume.get("jd_match_details", {})

        if request.include_deep_analysis:
            record["deep_analysis"] = resume.get("deep_analysis", {})

        export_data.append(record)

    # Create export
    if request.format == "csv":
        content = _generate_csv(export_data, request)
    else:
        content = json.dumps(export_data, indent=2, default=str)

    export = await store.create_export(batch_id, content, request.format)

    if not export:
        raise HTTPException(status_code=500, detail="Failed to create export")

    return ExportResponse(
        export_id=export["export_id"],
        batch_id=batch_id,
        format=request.format,
        download_url=export["download_url"],
        created_at=datetime.fromisoformat(export["created_at"]),
        expires_at=datetime.utcnow() + timedelta(hours=1),
        record_count=len(export_data),
    )


@router.get("/{batch_id}/exports")
async def list_exports(batch_id: str):
    """List all exports for a batch."""
    store = get_store()

    batch = await store.get_batch(batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    exports = await store.list_exports(batch_id)

    return {
        "batch_id": batch_id,
        "exports": exports,
    }


def _generate_csv(data: List[dict], request: ExportRequest) -> str:
    """Generate CSV content from export data."""
    if not data:
        return ""

    output = io.StringIO()

    # Flatten nested structures for CSV
    flat_data = []
    for record in data:
        flat = {
            "resume_id": record.get("resume_id"),
            "filename": record.get("filename"),
            "rank": record.get("rank"),
            "status": record.get("status"),
            "overall_score": record.get("overall_score"),
        }

        # Flatten scores
        scores = record.get("scores", {})
        for key, value in scores.items():
            flat[f"score_{key}"] = value

        # Flatten extracted data
        if request.include_extracted_data:
            extracted = record.get("extracted_data", {})
            flat["name"] = extracted.get("name")
            flat["email"] = extracted.get("email")
            flat["phone"] = extracted.get("phone")
            flat["years_experience"] = extracted.get("years_of_experience")
            flat["skills"] = ", ".join(extracted.get("skills", []))

        # JD match
        if request.include_jd_match:
            flat["jd_match_score"] = record.get("jd_match_score")

        flat_data.append(flat)

    # Write CSV
    if flat_data:
        writer = csv.DictWriter(output, fieldnames=flat_data[0].keys())
        writer.writeheader()
        writer.writerows(flat_data)

    return output.getvalue()
