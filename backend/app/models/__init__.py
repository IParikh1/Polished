"""
Models module for Polished Resume Ranking System.
"""

from .batch_schemas import (
    # Enums
    BatchStatus,
    ResumeStatus,
    PremiumFeature,
    PlacementStatus,
    # Request schemas
    BatchCreateRequest,
    ResumeUploadRequest,
    BatchUploadRequest,
    BatchUpdateRequest,
    ScoreFilterRequest,
    ExportRequest,
    PlacementCreateRequest,
    PlacementVerifyRequest,
    # Response schemas
    ScoreBreakdown,
    ExtractedResumeData,
    JDMatchDetails,
    DeepAnalysis,
    ResumeResponse,
    BatchResponse,
    BatchListResponse,
    RankingResponse,
    UploadUrlResponse,
    BatchUploadResponse,
    ExportResponse,
    PlacementResponse,
    PlacementListResponse,
    PlacementStatsResponse,
    ErrorResponse,
    ValidationErrorResponse,
    # Utility functions
    generate_batch_id,
    generate_resume_id,
    generate_placement_id,
    generate_export_id,
)

__all__ = [
    # Enums
    "BatchStatus",
    "ResumeStatus",
    "PremiumFeature",
    "PlacementStatus",
    # Request schemas
    "BatchCreateRequest",
    "ResumeUploadRequest",
    "BatchUploadRequest",
    "BatchUpdateRequest",
    "ScoreFilterRequest",
    "ExportRequest",
    "PlacementCreateRequest",
    "PlacementVerifyRequest",
    # Response schemas
    "ScoreBreakdown",
    "ExtractedResumeData",
    "JDMatchDetails",
    "DeepAnalysis",
    "ResumeResponse",
    "BatchResponse",
    "BatchListResponse",
    "RankingResponse",
    "UploadUrlResponse",
    "BatchUploadResponse",
    "ExportResponse",
    "PlacementResponse",
    "PlacementListResponse",
    "PlacementStatsResponse",
    "ErrorResponse",
    "ValidationErrorResponse",
    # Utility functions
    "generate_batch_id",
    "generate_resume_id",
    "generate_placement_id",
    "generate_export_id",
]
