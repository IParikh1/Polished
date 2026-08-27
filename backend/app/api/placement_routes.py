"""
Placement Tracking API Routes for Polished Resume Ranking System.
Handles placement reporting, verification, and revenue tracking.
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional, List
from datetime import datetime

from ..models.batch_schemas import (
    PlacementCreateRequest,
    PlacementVerifyRequest,
    PlacementResponse,
    PlacementListResponse,
    PlacementStatsResponse,
    PlacementStatus,
    generate_placement_id,
)
from ..services.aws_store import get_store
from ..services.premium_gate import get_premium_gate, PremiumFeature
from ..middleware.auth import get_current_user, AuthenticatedUser
from ..middleware.admin import get_current_admin
from .batch_routes import verify_batch_ownership


router = APIRouter(prefix="/placements", tags=["Placements"])


# ==================== Placement CRUD Operations ====================

@router.post("", response_model=PlacementResponse)
async def report_placement(
    request: PlacementCreateRequest,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Report a new placement for revenue tracking.

    Placement fee is $250 per verified placement.
    """
    store = get_store()
    gate = get_premium_gate()

    # Verify the caller owns the batch (also confirms it exists)
    batch = await verify_batch_ownership(request.batch_id, user.user_id)

    resume = await store.get_resume(request.batch_id, request.resume_id)
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    # Create placement
    placement_data = {
        "placement_id": generate_placement_id(),
        "reported_by": user.user_id,
        "batch_id": request.batch_id,
        "resume_id": request.resume_id,
        "company_name": request.company_name,
        "position": request.position,
        "candidate_name": request.candidate_name or resume.get("extracted_data", {}).get("name"),
        "placement_date": request.placement_date.isoformat() if request.placement_date else datetime.utcnow().isoformat(),
        "notes": request.notes,
        "fee_amount": 250.00,
    }

    placement = await store.create_placement(placement_data)

    return PlacementResponse(
        placement_id=placement["placement_id"],
        batch_id=placement["batch_id"],
        resume_id=placement["resume_id"],
        company_name=placement["company_name"],
        position=placement["position"],
        candidate_name=placement.get("candidate_name"),
        placement_date=datetime.fromisoformat(placement["placement_date"]),
        reported_at=datetime.fromisoformat(placement["reported_at"]),
        verification_status=PlacementStatus(placement["verification_status"]),
        fee_amount=float(placement["fee_amount"]),
        fee_paid=placement.get("fee_paid", False),
        notes=placement.get("notes"),
    )


@router.get("", response_model=PlacementListResponse)
async def list_placements(
    batch_id: Optional[str] = Query(None, description="Filter by batch ID"),
    status: Optional[PlacementStatus] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=200),
    admin: AuthenticatedUser = Depends(get_current_admin),
):
    """
    List all placements with optional filters.
    """
    store = get_store()

    placements = await store.list_placements(
        batch_id=batch_id,
        status=status.value if status else None,
        limit=limit,
    )

    placement_responses = [
        PlacementResponse(
            placement_id=p["placement_id"],
            batch_id=p["batch_id"],
            resume_id=p["resume_id"],
            company_name=p["company_name"],
            position=p["position"],
            candidate_name=p.get("candidate_name"),
            placement_date=datetime.fromisoformat(p["placement_date"]),
            reported_at=datetime.fromisoformat(p["reported_at"]),
            verification_status=PlacementStatus(p["verification_status"]),
            fee_amount=float(p["fee_amount"]),
            fee_paid=p.get("fee_paid", False),
            verification_details=p.get("verification_details"),
            notes=p.get("notes"),
        )
        for p in placements
    ]

    # Get stats
    stats = await store.get_placement_stats()

    return PlacementListResponse(
        placements=placement_responses,
        total=len(placement_responses),
        stats=stats,
    )


@router.get("/stats", response_model=PlacementStatsResponse)
async def get_placement_stats(admin: AuthenticatedUser = Depends(get_current_admin)):
    """
    Get aggregated placement statistics.

    Includes:
    - Total placements
    - Verified/pending/disputed counts
    - Total and pending revenue
    """
    store = get_store()
    stats = await store.get_placement_stats()

    return PlacementStatsResponse(
        total_placements=stats.get("total_placements", 0),
        verified=stats.get("verified", 0),
        pending=stats.get("pending", 0),
        disputed=stats.get("disputed", 0),
        total_revenue=stats.get("total_revenue", 0),
        pending_revenue=stats.get("pending_revenue", 0),
    )


@router.get("/{placement_id}", response_model=PlacementResponse)
async def get_placement(
    placement_id: str,
    admin: AuthenticatedUser = Depends(get_current_admin),
):
    """Get a specific placement by ID. Admin only."""
    store = get_store()

    placement = await store.get_placement(placement_id)
    if not placement:
        raise HTTPException(status_code=404, detail="Placement not found")

    return PlacementResponse(
        placement_id=placement["placement_id"],
        batch_id=placement["batch_id"],
        resume_id=placement["resume_id"],
        company_name=placement["company_name"],
        position=placement["position"],
        candidate_name=placement.get("candidate_name"),
        placement_date=datetime.fromisoformat(placement["placement_date"]),
        reported_at=datetime.fromisoformat(placement["reported_at"]),
        verification_status=PlacementStatus(placement["verification_status"]),
        fee_amount=float(placement["fee_amount"]),
        fee_paid=placement.get("fee_paid", False),
        verification_details=placement.get("verification_details"),
        notes=placement.get("notes"),
    )


# ==================== Verification Operations ====================

@router.post("/{placement_id}/verify", response_model=PlacementResponse)
async def verify_placement(
    placement_id: str,
    request: PlacementVerifyRequest,
    admin: AuthenticatedUser = Depends(get_current_admin),
):
    """
    Verify or dispute a placement.

    Once verified, the placement fee becomes payable.
    """
    store = get_store()

    placement = await store.get_placement(placement_id)
    if not placement:
        raise HTTPException(status_code=404, detail="Placement not found")

    # Determine new status
    if request.verified:
        new_status = PlacementStatus.VERIFIED.value
    else:
        new_status = PlacementStatus.DISPUTED.value

    # Update placement
    verification_details = {
        "method": request.verification_method,
        "verified_at": datetime.utcnow().isoformat(),
        **(request.verification_details or {}),
    }

    success = await store.update_placement_status(
        placement_id,
        new_status,
        verification_details,
    )

    if not success:
        raise HTTPException(status_code=500, detail="Failed to update placement")

    # Fetch updated placement
    updated = await store.get_placement(placement_id)

    return PlacementResponse(
        placement_id=updated["placement_id"],
        batch_id=updated["batch_id"],
        resume_id=updated["resume_id"],
        company_name=updated["company_name"],
        position=updated["position"],
        candidate_name=updated.get("candidate_name"),
        placement_date=datetime.fromisoformat(updated["placement_date"]),
        reported_at=datetime.fromisoformat(updated["reported_at"]),
        verification_status=PlacementStatus(updated["verification_status"]),
        fee_amount=float(updated["fee_amount"]),
        fee_paid=updated.get("fee_paid", False),
        verification_details=updated.get("verification_details"),
        notes=updated.get("notes"),
    )


@router.post("/{placement_id}/dispute")
async def dispute_placement(
    placement_id: str,
    reason: str = Query(..., min_length=10, max_length=1000),
    user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Dispute a placement verification.
    """
    store = get_store()

    placement = await store.get_placement(placement_id)
    if not placement:
        raise HTTPException(status_code=404, detail="Placement not found")

    verification_details = {
        "dispute_reason": reason,
        "disputed_at": datetime.utcnow().isoformat(),
        **(placement.get("verification_details") or {}),
    }

    success = await store.update_placement_status(
        placement_id,
        PlacementStatus.DISPUTED.value,
        verification_details,
    )

    if not success:
        raise HTTPException(status_code=500, detail="Failed to dispute placement")

    return {"message": "Placement disputed", "placement_id": placement_id}


# ==================== Payment Operations ====================

@router.post("/{placement_id}/mark-paid")
async def mark_placement_paid(
    placement_id: str,
    admin: AuthenticatedUser = Depends(get_current_admin),
):
    """
    Mark a placement fee as paid.

    Only verified placements can be marked as paid.
    """
    store = get_store()

    placement = await store.get_placement(placement_id)
    if not placement:
        raise HTTPException(status_code=404, detail="Placement not found")

    if placement["verification_status"] != PlacementStatus.VERIFIED.value:
        raise HTTPException(
            status_code=400,
            detail="Only verified placements can be marked as paid"
        )

    if placement.get("fee_paid"):
        raise HTTPException(status_code=400, detail="Placement already marked as paid")

    success = await store.mark_placement_paid(placement_id)

    if not success:
        raise HTTPException(status_code=500, detail="Failed to mark placement as paid")

    return {
        "message": "Placement marked as paid",
        "placement_id": placement_id,
        "fee_amount": float(placement["fee_amount"]),
    }


# ==================== Batch Placement Operations ====================

@router.get("/batch/{batch_id}")
async def get_batch_placements(
    batch_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Get all placements from a specific batch. Only accessible by the batch owner."""
    store = get_store()

    batch = await verify_batch_ownership(batch_id, user.user_id)

    placements = await store.list_placements(batch_id=batch_id)

    # Calculate batch-specific stats
    total_placements = len(placements)
    verified = sum(1 for p in placements if p["verification_status"] == "verified")
    total_revenue = sum(
        float(p["fee_amount"])
        for p in placements
        if p.get("fee_paid")
    )
    pending_revenue = sum(
        float(p["fee_amount"])
        for p in placements
        if p["verification_status"] == "verified" and not p.get("fee_paid")
    )

    return {
        "batch_id": batch_id,
        "batch_name": batch.get("name"),
        "placements": [
            {
                "placement_id": p["placement_id"],
                "resume_id": p["resume_id"],
                "company_name": p["company_name"],
                "position": p["position"],
                "candidate_name": p.get("candidate_name"),
                "verification_status": p["verification_status"],
                "fee_paid": p.get("fee_paid", False),
            }
            for p in placements
        ],
        "stats": {
            "total_placements": total_placements,
            "verified": verified,
            "total_revenue": total_revenue,
            "pending_revenue": pending_revenue,
        },
    }
