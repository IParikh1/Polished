"""
AWS Storage Service for Polished Resume Ranking System.
Unified interface for DynamoDB and S3 operations.
"""

from typing import Dict, List, Optional, Any, BinaryIO, Union
from datetime import datetime
import json

from ..aws.dynamodb import get_db, DynamoDBClient
from ..aws.s3 import get_s3, S3Client
from ..models.batch_schemas import (
    BatchStatus,
    ResumeStatus,
    generate_batch_id,
    generate_resume_id,
    generate_export_id,
)


class AWSStore:
    """
    Unified storage interface for AWS services.
    Combines DynamoDB and S3 operations.
    """

    def __init__(self):
        self.db: DynamoDBClient = get_db()
        self.s3: S3Client = get_s3()

    # ==================== Batch Operations ====================

    async def create_batch(
        self,
        name: Optional[str] = None,
        user_id: str = "anonymous",
        job_description: Optional[str] = None,
        premium_features: Optional[List[str]] = None,
        settings: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new batch with metadata in DynamoDB and S3.

        Returns:
            Complete batch record
        """
        batch_id = generate_batch_id()

        # Create DynamoDB record
        batch_data = {
            "batch_id": batch_id,
            "user_id": user_id,
            "name": name or f"Batch {batch_id[:12]}",
            "status": BatchStatus.PENDING.value,
            "total_resumes": 0,
            "processed_resumes": 0,
            "job_description": job_description,
            "premium_features": premium_features or [],
            "settings": settings or {},
        }

        batch = self.db.create_batch(batch_data)

        # Create S3 metadata
        self.s3.save_batch_metadata(batch_id, {
            "batch_id": batch_id,
            "created_at": batch["created_at"],
            "settings": settings or {}
        })

        return batch

    async def get_batch(self, batch_id: str) -> Optional[Dict[str, Any]]:
        """Get batch by ID."""
        return self.db.get_batch(batch_id)

    async def list_batches(
        self,
        user_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """List batches, optionally filtered by user."""
        return self.db.list_batches(user_id, limit)

    async def update_batch(
        self,
        batch_id: str,
        **updates
    ) -> Optional[Dict[str, Any]]:
        """Update batch fields."""
        batch = await self.get_batch(batch_id)
        if not batch:
            return None

        # Update allowed fields
        for key, value in updates.items():
            if key in ["name", "job_description", "premium_features", "settings"]:
                batch[key] = value

        batch["updated_at"] = datetime.utcnow().isoformat()

        # Re-create with updates (DynamoDB put_item)
        self.db.create_batch(batch)
        return batch

    async def update_batch_status(
        self,
        batch_id: str,
        status: BatchStatus,
        processed_resumes: Optional[int] = None
    ) -> bool:
        """Update batch status and progress."""
        return self.db.update_batch_status(
            batch_id,
            status.value,
            processed_resumes
        )

    async def delete_batch(self, batch_id: str) -> bool:
        """Delete batch and all associated data."""
        # Delete S3 files
        self.s3.delete_batch_files(batch_id)

        # Delete DynamoDB records
        return self.db.delete_batch(batch_id)

    # ==================== Resume Operations ====================

    async def add_resume(
        self,
        batch_id: str,
        filename: str,
        file_content: Optional[Union[bytes, BinaryIO]] = None,
        content_type: Optional[str] = None,
        target_role: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Add a resume to a batch.

        If file_content is provided, uploads to S3.
        Otherwise, returns upload URL for direct upload.
        """
        resume_id = generate_resume_id()
        s3_key = None

        if file_content:
            # Upload file to S3
            s3_key = self.s3.upload_resume(
                batch_id,
                resume_id,
                file_content,
                filename,
                content_type
            )

        # Create DynamoDB record
        resume_data = {
            "batch_id": batch_id,
            "resume_id": resume_id,
            "filename": filename,
            "s3_key": s3_key,
            "status": ResumeStatus.PENDING.value if s3_key else ResumeStatus.UPLOADING.value,
        }

        if target_role:
            resume_data["target_role"] = target_role

        resume = self.db.add_resume_to_batch(resume_data)

        # Update batch resume count
        batch = await self.get_batch(batch_id)
        if batch:
            self.db.update_batch_status(
                batch_id,
                batch["status"],
                batch.get("total_resumes", 0) + 1
            )
            # Also update total_resumes
            batch["total_resumes"] = batch.get("total_resumes", 0) + 1
            self.db.create_batch(batch)

        return resume

    async def get_resume_upload_url(
        self,
        batch_id: str,
        resume_id: str,
        filename: str
    ) -> Optional[Dict[str, str]]:
        """Get presigned URL for direct resume upload."""
        return self.s3.generate_upload_url(batch_id, resume_id, filename)

    async def confirm_resume_upload(
        self,
        batch_id: str,
        resume_id: str,
        s3_key: str
    ) -> bool:
        """Confirm resume upload and update status."""
        resume = self.db.get_resume(batch_id, resume_id)
        if not resume:
            return False

        resume["s3_key"] = s3_key
        resume["status"] = ResumeStatus.PENDING.value
        resume["updated_at"] = datetime.utcnow().isoformat()

        self.db.add_resume_to_batch(resume)
        return True

    async def get_resume(
        self,
        batch_id: str,
        resume_id: str,
        include_download_url: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Get resume by ID."""
        resume = self.db.get_resume(batch_id, resume_id)

        if resume and include_download_url and resume.get("s3_key"):
            resume["download_url"] = self.s3.get_resume_url(resume["s3_key"])

        return resume

    async def get_batch_resumes(
        self,
        batch_id: str,
        sort_by_score: bool = True,
        include_download_urls: bool = False
    ) -> List[Dict[str, Any]]:
        """Get all resumes in a batch."""
        resumes = self.db.get_batch_resumes(batch_id, sort_by_score)

        if include_download_urls:
            for resume in resumes:
                if resume.get("s3_key"):
                    resume["download_url"] = self.s3.get_resume_url(resume["s3_key"])

        return resumes

    async def get_resume_content(
        self,
        batch_id: str,
        resume_id: str
    ) -> Optional[bytes]:
        """Download resume file content."""
        resume = self.db.get_resume(batch_id, resume_id)
        if not resume or not resume.get("s3_key"):
            return None

        return self.s3.get_resume(resume["s3_key"])

    async def update_resume_scores(
        self,
        batch_id: str,
        resume_id: str,
        scores: Dict[str, float],
        overall_score: float,
        rank: Optional[int] = None
    ) -> bool:
        """Update resume scores."""
        return self.db.update_resume_scores(
            batch_id,
            resume_id,
            scores,
            overall_score,
            rank
        )

    async def update_resume_extracted_data(
        self,
        batch_id: str,
        resume_id: str,
        extracted_data: Dict[str, Any]
    ) -> bool:
        """Store extracted resume data."""
        resume = self.db.get_resume(batch_id, resume_id)
        if not resume:
            return False

        resume["extracted_data"] = extracted_data
        resume["updated_at"] = datetime.utcnow().isoformat()

        self.db.add_resume_to_batch(resume)
        return True

    async def update_resume_jd_match(
        self,
        batch_id: str,
        resume_id: str,
        jd_match_score: float,
        match_details: Optional[Dict] = None
    ) -> bool:
        """Update JD matching score."""
        return self.db.update_resume_jd_match(
            batch_id,
            resume_id,
            jd_match_score,
            match_details
        )

    async def update_resume_deep_analysis(
        self,
        batch_id: str,
        resume_id: str,
        analysis: Dict[str, Any]
    ) -> bool:
        """Store deep analysis results."""
        return self.db.update_resume_deep_analysis(
            batch_id,
            resume_id,
            analysis
        )

    # ==================== Export Operations ====================

    async def create_export(
        self,
        batch_id: str,
        content: Union[str, Dict, List],
        format_type: str = "json"
    ) -> Dict[str, Any]:
        """
        Create an export file and store in S3.

        Returns:
            Export metadata with download URL
        """
        export_id = generate_export_id()

        # Convert content to string if needed
        if format_type == "json" and not isinstance(content, str):
            content = json.dumps(content, default=str, indent=2)

        # Save to S3
        s3_key = self.s3.save_export(batch_id, export_id, content, format_type)

        if not s3_key:
            return None

        # Generate download URL
        download_url = self.s3.get_export_url(s3_key)

        return {
            "export_id": export_id,
            "batch_id": batch_id,
            "format": format_type,
            "s3_key": s3_key,
            "download_url": download_url,
            "created_at": datetime.utcnow().isoformat()
        }

    async def list_exports(self, batch_id: str) -> List[Dict[str, Any]]:
        """List all exports for a batch."""
        exports = self.s3.list_exports(batch_id)

        # Add download URLs
        for export in exports:
            export["download_url"] = self.s3.get_export_url(export["key"])

        return exports

    # ==================== Placement Operations ====================

    async def create_placement(
        self,
        placement_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a new placement record."""
        return self.db.create_placement(placement_data)

    async def get_placement(self, placement_id: str) -> Optional[Dict[str, Any]]:
        """Get placement by ID."""
        return self.db.get_placement(placement_id)

    async def list_placements(
        self,
        batch_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """List placements with optional filters."""
        return self.db.list_placements(batch_id, status, limit)

    async def update_placement_status(
        self,
        placement_id: str,
        status: str,
        verification_details: Optional[Dict] = None
    ) -> bool:
        """Update placement verification status."""
        return self.db.update_placement_status(
            placement_id,
            status,
            verification_details
        )

    async def mark_placement_paid(self, placement_id: str) -> bool:
        """Mark placement fee as paid."""
        return self.db.mark_placement_paid(placement_id)

    async def get_placement_stats(self) -> Dict[str, Any]:
        """Get aggregated placement statistics."""
        return self.db.get_placement_stats()


# Singleton instance
_aws_store: Optional[AWSStore] = None


def get_store() -> AWSStore:
    """Get the AWS store singleton."""
    global _aws_store
    if _aws_store is None:
        _aws_store = AWSStore()
    return _aws_store
