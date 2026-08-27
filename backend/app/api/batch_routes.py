"""
Batch API Routes for Polished Resume Ranking System.
Handles batch creation, resume upload, scoring, and export.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Query, BackgroundTasks, Depends, Form
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
    SalesRole,
    JDMatchRequest,
    JDMatchResult,
    TailoredResumeRequest,
    TailoredResumeResponse,
    SetRoleRequest,
    SetRoleResponse,
    generate_batch_id,
    generate_resume_id,
    generate_export_id,
)
from ..services.aws_store import get_store
from ..services.batch_processor import get_processor
from ..services.batch_cache import get_cache
from ..services.premium_gate import get_premium_gate, PremiumFeature
from ..services.jd_matcher import get_tech_sales_matcher, parse_job_description
from ..middleware.auth import get_current_user, AuthenticatedUser


router = APIRouter(prefix="/batches", tags=["Batches"])


# ==================== Helper Functions ====================

# Upload constraints
MAX_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB per resume file
ALLOWED_UPLOAD_EXTENSIONS = [".pdf", ".doc", ".docx", ".txt", ".rtf"]


def sanitize_filename(filename: str) -> str:
    """
    Strip path components and dangerous characters from an uploaded filename
    so it can't inject path segments into S3 keys.
    """
    import os as _os
    import re as _re
    # Strip any directory components (handles both / and \)
    name = _os.path.basename(filename.replace("\\", "/"))
    # Keep a conservative character set
    name = _re.sub(r"[^A-Za-z0-9._ ()-]", "_", name).strip(". ")
    return name[:200] or "resume"


def validate_upload_file(filename: str, content: bytes) -> str:
    """
    Validate an uploaded file's extension and size.
    Returns the sanitized filename, or raises HTTPException.
    """
    safe_name = sanitize_filename(filename or "")
    ext = "." + safe_name.lower().split(".")[-1] if "." in safe_name else ""
    if ext not in ALLOWED_UPLOAD_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type {ext or '(none)'} not supported. Allowed: {ALLOWED_UPLOAD_EXTENSIONS}"
        )
    if len(content) > MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File too large ({len(content)} bytes). Max {MAX_UPLOAD_SIZE_BYTES // (1024*1024)} MB."
        )
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Empty file")
    return safe_name


async def verify_batch_ownership(batch_id: str, user_id: str) -> dict:
    """
    Verify that a user owns a batch. Returns the batch if owned.
    Raises 404 if batch not found, 403 if not owned.
    """
    store = get_store()
    batch = await store.get_batch(batch_id)

    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    if batch.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="Access denied - you don't own this batch")

    return batch


# ==================== Batch CRUD Operations ====================

@router.post("", response_model=BatchResponse)
async def create_batch(
    request: BatchCreateRequest,
    user: AuthenticatedUser = Depends(get_current_user)
):
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
            user.user_id,
            [f.value for f in request.premium_features]
        )
        if not validation["valid"]:
            raise HTTPException(
                status_code=402,
                detail={
                    "error": "Premium features not available",
                    "denied_features": validation["denied_features"],
                    "upgrade_options": gate.get_upgrade_options(user.user_id)
                }
            )

    batch = await store.create_batch(
        name=request.name,
        user_id=user.user_id,
        job_description=request.job_description,
        premium_features=[f.value for f in request.premium_features] if request.premium_features else [],
        settings=request.settings,
    )

    # Cache the batch
    cache = get_cache()
    cache.cache_batch(batch["batch_id"], batch)

    # Record usage for admin tracking
    try:
        from ..aws.dynamodb import get_db
        db = get_db()
        db.record_usage(user.user_id, "batches_created", 1)
    except Exception as e:
        print(f"Error recording usage: {e}")

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
    user: AuthenticatedUser = Depends(get_current_user)
):
    """List all batches with pagination. Only returns batches owned by the current user."""
    store = get_store()
    batches = await store.list_batches(user_id=user.user_id, limit=limit)

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
async def get_batch(
    batch_id: str,
    user: AuthenticatedUser = Depends(get_current_user)
):
    """Get batch by ID. Only accessible by the batch owner."""
    # Verify ownership (this also returns the batch)
    batch = await verify_batch_ownership(batch_id, user.user_id)

    # Cache for next time
    cache = get_cache()
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
async def update_batch(
    batch_id: str,
    request: BatchUpdateRequest,
    user: AuthenticatedUser = Depends(get_current_user)
):
    """Update batch settings. Only accessible by the batch owner."""
    store = get_store()
    cache = get_cache()

    # Verify ownership
    await verify_batch_ownership(batch_id, user.user_id)

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
async def delete_batch(
    batch_id: str,
    user: AuthenticatedUser = Depends(get_current_user)
):
    """Delete a batch and all associated data. Only accessible by the batch owner."""
    store = get_store()
    cache = get_cache()

    # Verify ownership
    await verify_batch_ownership(batch_id, user.user_id)

    success = await store.delete_batch(batch_id)

    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete batch")

    # Invalidate cache
    cache.invalidate_batch(batch_id)

    return {"message": "Batch deleted successfully"}


@router.post("/{batch_id}/close", response_model=BatchResponse)
async def close_batch(
    batch_id: str,
    user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Manually close a batch to view rankings without waiting for processing.

    This allows users to:
    - View the ranking table for resumes that have been uploaded
    - See partial rankings even if not all resumes are processed
    - Stop accepting new uploads for this batch

    The batch status changes to 'completed' so rankings become visible.
    Only batches with status 'pending' or 'processing' can be closed.
    """
    store = get_store()
    cache = get_cache()

    # Verify ownership
    batch = await verify_batch_ownership(batch_id, user.user_id)

    # Only allow closing pending or processing batches
    if batch["status"] not in ["pending", "processing"]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot close batch with status '{batch['status']}'. Only pending or processing batches can be closed."
        )

    # Check if batch has any resumes
    if batch.get("total_resumes", 0) == 0:
        raise HTTPException(
            status_code=400,
            detail="Cannot close an empty batch. Upload at least one resume first."
        )

    # Update status to completed
    success = await store.update_batch_status(batch_id, BatchStatus.COMPLETED)

    if not success:
        raise HTTPException(status_code=500, detail="Failed to close batch")

    # Invalidate cache
    cache.invalidate_batch(batch_id)

    # Get updated batch
    updated_batch = await store.get_batch(batch_id)

    return BatchResponse(
        batch_id=updated_batch["batch_id"],
        name=updated_batch["name"],
        status=BatchStatus(updated_batch["status"]),
        total_resumes=updated_batch.get("total_resumes", 0),
        processed_resumes=updated_batch.get("processed_resumes", 0),
        created_at=datetime.fromisoformat(updated_batch["created_at"]),
        updated_at=datetime.fromisoformat(updated_batch["updated_at"]),
        job_description=updated_batch.get("job_description"),
        premium_features=updated_batch.get("premium_features", []),
        settings=updated_batch.get("settings", {}),
    )


@router.post("/{batch_id}/reopen", response_model=BatchResponse)
async def reopen_batch(
    batch_id: str,
    user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Reopen a completed batch to allow adding more resumes.

    This changes the batch status back to 'pending' so users can:
    - Upload additional resumes
    - Re-process all resumes together
    - Get updated rankings

    Only batches with status 'completed' or 'failed' can be reopened.
    """
    store = get_store()
    cache = get_cache()

    # Verify ownership
    batch = await verify_batch_ownership(batch_id, user.user_id)

    # Only allow reopening completed or failed batches
    if batch["status"] not in ["completed", "failed"]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot reopen batch with status '{batch['status']}'. Only completed or failed batches can be reopened."
        )

    # Update status to pending
    success = await store.update_batch_status(batch_id, BatchStatus.PENDING)

    if not success:
        raise HTTPException(status_code=500, detail="Failed to reopen batch")

    # Invalidate cache
    cache.invalidate_batch(batch_id)

    # Get updated batch
    updated_batch = await store.get_batch(batch_id)

    return BatchResponse(
        batch_id=updated_batch["batch_id"],
        name=updated_batch["name"],
        status=BatchStatus(updated_batch["status"]),
        total_resumes=updated_batch.get("total_resumes", 0),
        processed_resumes=updated_batch.get("processed_resumes", 0),
        created_at=datetime.fromisoformat(updated_batch["created_at"]),
        updated_at=datetime.fromisoformat(updated_batch["updated_at"]),
        job_description=updated_batch.get("job_description"),
        premium_features=updated_batch.get("premium_features", []),
        settings=updated_batch.get("settings", {}),
    )


# ==================== Resume Upload Operations ====================

@router.post("/{batch_id}/upload-urls", response_model=BatchUploadResponse)
async def get_upload_urls(
    batch_id: str,
    filenames: List[str] = Query(..., description="List of filenames to upload"),
    user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Get presigned URLs for direct upload to S3.

    Returns upload URLs for each file that can be used for direct PUT requests.
    """
    store = get_store()

    # Verify ownership
    await verify_batch_ownership(batch_id, user.user_id)

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
    target_role: Optional[SalesRole] = None,
    user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Upload a single resume file directly.

    Supports: PDF, DOCX, DOC, TXT, RTF

    - **target_role**: Optional target sales role for optimized analysis
    """
    store = get_store()

    # Verify ownership
    await verify_batch_ownership(batch_id, user.user_id)

    # Read and validate file (type, size, sanitized name)
    content = await file.read()
    safe_name = validate_upload_file(file.filename, content)

    # Add resume with target role
    resume = await store.add_resume(
        batch_id,
        safe_name,
        file_content=content,
        content_type=file.content_type,
        target_role=target_role.value if target_role else None,
    )

    return {
        "resume_id": resume["resume_id"],
        "filename": resume["filename"],
        "status": resume["status"],
        "target_role": target_role.value if target_role else None,
    }


@router.post("/{batch_id}/upload-multiple")
async def upload_multiple_resumes(
    batch_id: str,
    files: List[UploadFile] = File(...),
    target_role: Optional[SalesRole] = None,
    role_mapping: Optional[str] = Form(None),
    user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Upload multiple resume files at once.

    - **target_role**: Optional target sales role for optimized analysis (applies to all files)
    - **role_mapping**: Optional JSON string mapping filenames to roles for per-file role assignment
                       Example: {"resume1.pdf": "sdr", "resume2.pdf": "account_executive"}
    """
    import json

    store = get_store()

    # Verify ownership
    await verify_batch_ownership(batch_id, user.user_id)

    # Parse role mapping if provided
    file_role_map = {}
    if role_mapping:
        try:
            file_role_map = json.loads(role_mapping)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid role_mapping JSON format")

    results = []
    default_role_value = target_role.value if target_role else None
    valid_roles = {r.value for r in SalesRole}

    for file in files:
        # Get role for this specific file, or fall back to default
        file_role = file_role_map.get(file.filename, default_role_value)
        if file_role is not None and file_role not in valid_roles:
            results.append({
                "filename": file.filename,
                "status": "error",
                "error": f"Invalid target role: {file_role}"
            })
            continue

        try:
            content = await file.read()
            safe_name = validate_upload_file(file.filename, content)
            resume = await store.add_resume(
                batch_id,
                safe_name,
                file_content=content,
                content_type=file.content_type,
                target_role=file_role,
            )
            results.append({
                "resume_id": resume["resume_id"],
                "filename": resume["filename"],
                "status": "uploaded",
                "target_role": file_role,
            })
        except HTTPException as e:
            results.append({
                "filename": file.filename,
                "status": "error",
                "error": e.detail if isinstance(e.detail, str) else "Validation failed"
            })
        except Exception:
            results.append({
                "filename": file.filename,
                "status": "error",
                "error": "Upload failed"
            })

    return {
        "batch_id": batch_id,
        "uploaded": len([r for r in results if r["status"] == "uploaded"]),
        "failed": len([r for r in results if r["status"] == "error"]),
        "results": results,
        "target_role": default_role_value,
    }


@router.post("/{batch_id}/resumes/{resume_id}/confirm-upload")
async def confirm_resume_upload(
    batch_id: str,
    resume_id: str,
    s3_key: str = Query(..., description="S3 key of uploaded file"),
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Confirm that a resume was uploaded successfully via presigned URL."""
    store = get_store()

    # Verify ownership
    await verify_batch_ownership(batch_id, user.user_id)

    # Only accept keys inside this batch's prefix
    if not s3_key.startswith(f"{batch_id}/"):
        raise HTTPException(status_code=400, detail="Invalid S3 key for this batch")

    success = await store.confirm_resume_upload(batch_id, resume_id, s3_key)

    if not success:
        raise HTTPException(status_code=404, detail="Resume not found")

    return {"message": "Upload confirmed", "resume_id": resume_id}


# ==================== Processing Operations ====================

@router.post("/{batch_id}/process")
async def process_batch(
    batch_id: str,
    background_tasks: BackgroundTasks,
    user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Start processing all resumes in a batch.

    This runs in the background and updates batch status.
    """
    store = get_store()
    processor = get_processor()
    cache = get_cache()

    # Verify ownership
    await verify_batch_ownership(batch_id, user.user_id)

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
async def get_processing_status(
    batch_id: str,
    user: AuthenticatedUser = Depends(get_current_user)
):
    """Get the current processing status of a batch."""
    cache = get_cache()

    # Verify ownership (returns the batch)
    batch = await verify_batch_ownership(batch_id, user.user_id)

    # Check cache for real-time status
    cached_status = cache.get_processing_status(batch_id)

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
    user: AuthenticatedUser = Depends(get_current_user)
):
    """Get all resumes in a batch."""
    store = get_store()

    # Verify ownership
    await verify_batch_ownership(batch_id, user.user_id)

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
    user: AuthenticatedUser = Depends(get_current_user)
):
    """Get a specific resume with all its data."""
    store = get_store()

    # Verify ownership
    await verify_batch_ownership(batch_id, user.user_id)

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
    user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Get ranked resumes with optional filtering.

    Returns resumes sorted by overall score in descending order.
    """
    store = get_store()
    cache = get_cache()

    # Verify ownership
    await verify_batch_ownership(batch_id, user.user_id)

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
        # Handle empty scores dict - convert to None if empty or missing 'overall'
        scores_data = r.get("scores")
        if not scores_data or "overall" not in scores_data:
            scores_data = None

        resume_responses.append(ResumeResponse(
            resume_id=r["resume_id"],
            batch_id=r["batch_id"],
            filename=r["filename"],
            status=ResumeStatus(r.get("status", "pending")),
            created_at=datetime.fromisoformat(r["created_at"]),
            updated_at=datetime.fromisoformat(r["updated_at"]),
            rank=r.get("rank"),
            target_role=r.get("target_role"),
            scores=scores_data,
            extracted_data=r.get("extracted_data") or None,
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
async def export_batch(
    batch_id: str,
    request: ExportRequest,
    user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Export batch results to CSV or JSON.

    Returns a download URL for the export file.
    """
    store = get_store()
    gate = get_premium_gate()

    # Verify ownership
    await verify_batch_ownership(batch_id, user.user_id)

    # Check premium features if exporting premium data
    if request.include_deep_analysis and not gate.has_feature(user.user_id, PremiumFeature.DEEP_ANALYSIS):
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

    # Record usage for admin tracking
    try:
        from ..aws.dynamodb import get_db
        db = get_db()
        db.record_usage(user.user_id, "exports_count", 1)
    except Exception as e:
        print(f"Error recording export usage: {e}")

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
async def list_exports(
    batch_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """List all exports for a batch. Only accessible by the batch owner."""
    store = get_store()

    # Verify ownership
    await verify_batch_ownership(batch_id, user.user_id)

    exports = await store.list_exports(batch_id)

    return {
        "batch_id": batch_id,
        "exports": exports,
    }


# ==================== JD Matching Operations (Tech Sales) ====================

@router.post("/match-jd", response_model=JDMatchResult)
async def match_job_description(
    request: JDMatchRequest,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Match a resume against a job description.

    Returns detailed match analysis including:
    - Match score (0-100)
    - Matching and missing requirements
    - Keywords to add
    - Tailored suggestions for improvement

    Premium feature for tech sales resume optimization.
    """
    store = get_store()
    gate = get_premium_gate()

    # Validate premium access
    if not gate.has_feature(user.user_id, PremiumFeature.JD_MATCHING):
        raise HTTPException(
            status_code=402,
            detail={
                "error": "JD Matching is a premium feature",
                "upgrade_options": gate.get_upgrade_options(user.user_id)
            }
        )

    # Get resume text - either from batch or session
    resume_text = None
    resume_data = {}

    if request.batch_id and request.resume_id:
        # Verify ownership of the batch containing the resume
        await verify_batch_ownership(request.batch_id, user.user_id)
        resume = await store.get_resume(request.batch_id, request.resume_id)
        if not resume:
            raise HTTPException(status_code=404, detail="Resume not found")
        resume_text = await store.get_resume_text(request.batch_id, request.resume_id, resume=resume)
        resume_data = resume.get("extracted_data", {})
    else:
        raise HTTPException(
            status_code=400,
            detail="Must provide batch_id and resume_id"
        )

    if not resume_text:
        raise HTTPException(status_code=400, detail="Resume text not available")

    # Perform tech sales-specific matching
    matcher = get_tech_sales_matcher()
    result = await matcher.match_resume(
        resume_text=resume_text,
        resume_data=resume_data,
        job_description=request.job_description,
        target_role=request.target_role.value if request.target_role else None,
    )

    return JDMatchResult(
        match_score=int(result["match_score"]),
        matching_requirements=result.get("matching_requirements", []),
        gaps=result.get("gaps", []),
        keywords_to_add=result.get("keywords_to_add", []),
        keywords_present=result.get("keywords_present", []),
        tailored_suggestions=result.get("tailored_suggestions", []),
        experience_match=result.get("experience_match", False),
        skills_alignment=result.get("skills_alignment"),
    )


@router.post("/{batch_id}/resumes/{resume_id}/match-jd", response_model=JDMatchResult)
async def match_resume_to_jd(
    batch_id: str,
    resume_id: str,
    job_description: str,
    job_title: Optional[str] = None,
    target_role: Optional[SalesRole] = None,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Match a specific resume against a job description.

    Convenience endpoint that combines batch_id and resume_id in the path.
    """
    store = get_store()
    gate = get_premium_gate()

    # Verify ownership
    await verify_batch_ownership(batch_id, user.user_id)

    # Validate premium access
    if not gate.has_feature(user.user_id, PremiumFeature.JD_MATCHING):
        raise HTTPException(
            status_code=402,
            detail={
                "error": "JD Matching is a premium feature",
                "upgrade_options": gate.get_upgrade_options(user.user_id)
            }
        )

    # Get resume
    resume = await store.get_resume(batch_id, resume_id)
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    resume_text = await store.get_resume_text(batch_id, resume_id, resume=resume)
    resume_data = resume.get("extracted_data", {})

    if not resume_text:
        raise HTTPException(status_code=400, detail="Resume text not available")

    # Perform matching
    matcher = get_tech_sales_matcher()
    result = await matcher.match_resume(
        resume_text=resume_text,
        resume_data=resume_data,
        job_description=job_description,
        target_role=target_role.value if target_role else None,
    )

    return JDMatchResult(
        match_score=int(result["match_score"]),
        matching_requirements=result.get("matching_requirements", []),
        gaps=result.get("gaps", []),
        keywords_to_add=result.get("keywords_to_add", []),
        keywords_present=result.get("keywords_present", []),
        tailored_suggestions=result.get("tailored_suggestions", []),
        experience_match=result.get("experience_match", False),
        skills_alignment=result.get("skills_alignment"),
    )


@router.post("/tailor-resume", response_model=TailoredResumeResponse)
async def tailor_resume(
    request: TailoredResumeRequest,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Generate a JD-tailored version of a resume.

    Uses AI to rewrite the resume optimized for the specific job description,
    addressing gaps and incorporating missing keywords.

    Premium feature for tech sales resume optimization.
    """
    store = get_store()
    gate = get_premium_gate()

    # Validate premium access
    if not gate.has_feature(user.user_id, PremiumFeature.DEEP_ANALYSIS):
        raise HTTPException(
            status_code=402,
            detail={
                "error": "Resume tailoring is a premium feature",
                "upgrade_options": gate.get_upgrade_options(user.user_id)
            }
        )

    # Get resume text
    resume_text = None
    resume_data = {}

    if request.batch_id and request.resume_id:
        # Verify ownership of the batch containing the resume
        await verify_batch_ownership(request.batch_id, user.user_id)
        resume = await store.get_resume(request.batch_id, request.resume_id)
        if not resume:
            raise HTTPException(status_code=404, detail="Resume not found")
        resume_text = await store.get_resume_text(request.batch_id, request.resume_id, resume=resume)
        resume_data = resume.get("extracted_data", {})
    else:
        raise HTTPException(
            status_code=400,
            detail="Must provide batch_id and resume_id"
        )

    if not resume_text:
        raise HTTPException(status_code=400, detail="Resume text not available")

    # First, get the match analysis
    matcher = get_tech_sales_matcher()
    match_result = await matcher.match_resume(
        resume_text=resume_text,
        resume_data=resume_data,
        job_description=request.job_description,
        target_role=request.target_role.value if request.target_role else None,
    )

    # For now, return a structured response with the analysis
    # Full AI-powered rewriting will be implemented when LLM integration is added
    changes_needed = []
    metrics_needed = []

    # Identify changes based on gaps
    for gap in match_result.get("gaps", []):
        if "Experience" in gap:
            changes_needed.append("Reframe experience to emphasize relevant skills")
        elif "methodology" in gap.lower():
            changes_needed.append(f"Add sales methodology: {gap.split(':')[-1].strip()}")
        elif "tool" in gap.lower():
            changes_needed.append(f"Highlight tool proficiency: {gap.split(':')[-1].strip()}")
        elif "quota" in gap.lower():
            changes_needed.append("Add quantified quota attainment metrics")
            # Add metrics questions
            for exp in resume_data.get("experience", []):
                if exp.get("company"):
                    metrics_needed.append({
                        "company": exp["company"],
                        "role": exp.get("title", "Sales Role"),
                        "questions": [
                            "What was your annual/quarterly quota?",
                            "What percentage of quota did you achieve?",
                            "How many deals did you close per quarter?",
                        ]
                    })

    # Add keyword incorporation changes
    keywords_to_add = match_result.get("keywords_to_add", [])
    if keywords_to_add:
        changes_needed.append(f"Incorporate keywords: {', '.join(keywords_to_add[:5])}")

    # Calculate estimated improvement
    current_score = match_result.get("match_score", 50)
    estimated_improvement = min(100 - current_score, len(changes_needed) * 5 + len(keywords_to_add) * 2)

    return TailoredResumeResponse(
        tailored_resume=resume_text,  # Original for now - full rewriting needs LLM
        changes_made=changes_needed,
        metrics_needed=metrics_needed[:3],  # Limit to top 3 companies
        match_improvement=int(estimated_improvement),
    )


@router.post("/{batch_id}/resumes/{resume_id}/set-role", response_model=SetRoleResponse)
async def set_resume_role(
    batch_id: str,
    resume_id: str,
    request: SetRoleRequest,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Set the target sales role for a resume.

    Updates the resume record with the target role for optimized analysis.
    """
    store = get_store()

    # Verify ownership
    await verify_batch_ownership(batch_id, user.user_id)

    # Get resume
    resume = await store.get_resume(batch_id, resume_id)
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    # Update the target role
    await store.update_resume(
        batch_id,
        resume_id,
        target_role=request.role.value,
    )

    # Get display name
    role_display_names = {
        "entry_sdr": "Entry-Level SDR (0-1 years)",
        "sdr": "SDR/BDR (1-3 years)",
        "account_executive": "Account Executive (2-5 years)",
        "senior_ae": "Senior/Enterprise AE (5+ years)",
        "account_manager": "Account Manager / CSM",
        "sales_manager": "Sales Manager / Director",
    }

    return SetRoleResponse(
        message="Role updated successfully",
        role=request.role,
        role_display_name=role_display_names.get(request.role.value, request.role.value),
    )


@router.get("/parse-jd")
async def parse_jd(
    job_description: str,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Parse a job description and extract requirements.

    Utility endpoint for debugging and understanding JD parsing.
    Returns extracted requirements including:
    - Required skills
    - Experience requirements
    - Sales methodologies mentioned
    - Sales tools mentioned
    - Detected role type
    """
    result = parse_job_description(job_description, is_tech_sales=True)
    return result


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
