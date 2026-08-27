"""
S3 client utilities for Polished Resume Ranking System.
Handles resume storage, exports, and metadata.
"""

import boto3
from botocore.exceptions import ClientError
from typing import Dict, List, Optional, Any, BinaryIO, Union
from datetime import datetime, timedelta
import os
import json
import mimetypes

# AWS Configuration
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "polished-batches-us-east-1")

# Supported resume formats
SUPPORTED_FORMATS = {
    ".pdf": "application/pdf",
    ".doc": "application/msword",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".txt": "text/plain",
    ".rtf": "application/rtf",
}


def get_s3_client():
    """Get S3 client with configured region."""
    return boto3.client("s3", region_name=AWS_REGION)


def get_s3_resource():
    """Get S3 resource with configured region."""
    return boto3.resource("s3", region_name=AWS_REGION)


class S3Client:
    """Client for S3 operations."""

    def __init__(self, bucket_name: str = BUCKET_NAME):
        self.client = get_s3_client()
        self.resource = get_s3_resource()
        self.bucket_name = bucket_name

    # ==================== Bucket Operations ====================

    def ensure_bucket_exists(self) -> bool:
        """Ensure the S3 bucket exists, create if not."""
        try:
            self.client.head_bucket(Bucket=self.bucket_name)
            return True
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code")
            if error_code == "404":
                try:
                    if AWS_REGION == "us-east-1":
                        self.client.create_bucket(Bucket=self.bucket_name)
                    else:
                        self.client.create_bucket(
                            Bucket=self.bucket_name,
                            CreateBucketConfiguration={
                                "LocationConstraint": AWS_REGION
                            }
                        )

                    # Enable versioning for safety
                    self.client.put_bucket_versioning(
                        Bucket=self.bucket_name,
                        VersioningConfiguration={"Status": "Enabled"}
                    )

                    # Set lifecycle policy for old versions
                    self.client.put_bucket_lifecycle_configuration(
                        Bucket=self.bucket_name,
                        LifecycleConfiguration={
                            "Rules": [
                                {
                                    "ID": "DeleteOldVersions",
                                    "Status": "Enabled",
                                    "NoncurrentVersionExpiration": {
                                        "NoncurrentDays": 30
                                    },
                                    "Filter": {"Prefix": ""}
                                }
                            ]
                        }
                    )
                    return True
                except ClientError as create_error:
                    print(f"Error creating bucket: {create_error}")
                    return False
            print(f"Error checking bucket: {e}")
            return False

    # ==================== Resume Upload Operations ====================

    def upload_resume(
        self,
        batch_id: str,
        resume_id: str,
        file_content: Union[bytes, BinaryIO],
        filename: str,
        content_type: Optional[str] = None
    ) -> Optional[str]:
        """
        Upload a resume file to S3.

        Args:
            batch_id: The batch this resume belongs to
            resume_id: Unique resume identifier
            file_content: File content as bytes or file-like object
            filename: Original filename
            content_type: MIME type (auto-detected if not provided)

        Returns:
            S3 key if successful, None otherwise
        """
        # Determine content type
        if not content_type:
            ext = os.path.splitext(filename)[1].lower()
            content_type = SUPPORTED_FORMATS.get(ext, "application/octet-stream")

        s3_key = f"{batch_id}/resumes/{resume_id}/{filename}"

        try:
            if isinstance(file_content, bytes):
                self.client.put_object(
                    Bucket=self.bucket_name,
                    Key=s3_key,
                    Body=file_content,
                    ContentType=content_type,
                    ServerSideEncryption="AES256",
                    Metadata={
                        "batch_id": batch_id,
                        "resume_id": resume_id,
                        "original_filename": filename,
                        "uploaded_at": datetime.utcnow().isoformat()
                    }
                )
            else:
                self.client.upload_fileobj(
                    file_content,
                    self.bucket_name,
                    s3_key,
                    ExtraArgs={
                        "ContentType": content_type,
                        "ServerSideEncryption": "AES256",
                        "Metadata": {
                            "batch_id": batch_id,
                            "resume_id": resume_id,
                            "original_filename": filename,
                            "uploaded_at": datetime.utcnow().isoformat()
                        }
                    }
                )
            return s3_key
        except ClientError as e:
            print(f"Error uploading resume: {e}")
            return None

    def get_resume(self, s3_key: str) -> Optional[bytes]:
        """Download a resume from S3."""
        try:
            response = self.client.get_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            return response["Body"].read()
        except ClientError as e:
            print(f"Error downloading resume: {e}")
            return None

    def get_resume_url(
        self,
        s3_key: str,
        expiration: int = 3600
    ) -> Optional[str]:
        """
        Generate a presigned URL for resume download.

        Args:
            s3_key: The S3 key of the resume
            expiration: URL expiration time in seconds (default 1 hour)

        Returns:
            Presigned URL if successful, None otherwise
        """
        try:
            url = self.client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": s3_key},
                ExpiresIn=expiration
            )
            return url
        except ClientError as e:
            print(f"Error generating presigned URL: {e}")
            return None

    def generate_upload_url(
        self,
        batch_id: str,
        resume_id: str,
        filename: str,
        expiration: int = 3600
    ) -> Optional[Dict[str, str]]:
        """
        Generate a presigned URL for direct upload from frontend.

        Returns:
            Dictionary with 'url' and 's3_key' if successful
        """
        ext = os.path.splitext(filename)[1].lower()
        content_type = SUPPORTED_FORMATS.get(ext, "application/octet-stream")
        s3_key = f"{batch_id}/resumes/{resume_id}/{filename}"

        try:
            url = self.client.generate_presigned_url(
                "put_object",
                Params={
                    "Bucket": self.bucket_name,
                    "Key": s3_key,
                    "ContentType": content_type
                },
                ExpiresIn=expiration
            )
            return {"url": url, "s3_key": s3_key, "content_type": content_type}
        except ClientError as e:
            print(f"Error generating upload URL: {e}")
            return None

    def delete_resume(self, s3_key: str) -> bool:
        """Delete a resume from S3."""
        try:
            self.client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            return True
        except ClientError as e:
            print(f"Error deleting resume: {e}")
            return False

    def list_batch_resumes(self, batch_id: str) -> List[Dict[str, Any]]:
        """List all resumes in a batch."""
        prefix = f"{batch_id}/resumes/"

        try:
            response = self.client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )

            resumes = []
            for obj in response.get("Contents", []):
                resumes.append({
                    "key": obj["Key"],
                    "size": obj["Size"],
                    "last_modified": obj["LastModified"].isoformat(),
                })
            return resumes
        except ClientError as e:
            print(f"Error listing batch resumes: {e}")
            return []

    # ==================== Batch Metadata Operations ====================

    def save_batch_metadata(
        self,
        batch_id: str,
        metadata: Dict[str, Any]
    ) -> bool:
        """Save batch metadata to S3."""
        s3_key = f"{batch_id}/metadata.json"

        try:
            self.client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=json.dumps(metadata, default=str),
                ContentType="application/json",
                ServerSideEncryption="AES256",
            )
            return True
        except ClientError as e:
            print(f"Error saving batch metadata: {e}")
            return False

    def get_batch_metadata(self, batch_id: str) -> Optional[Dict[str, Any]]:
        """Get batch metadata from S3."""
        s3_key = f"{batch_id}/metadata.json"

        try:
            response = self.client.get_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            return json.loads(response["Body"].read().decode("utf-8"))
        except ClientError as e:
            print(f"Error getting batch metadata: {e}")
            return None

    # ==================== Export Operations ====================

    def save_export(
        self,
        batch_id: str,
        export_id: str,
        content: Union[str, bytes],
        format_type: str = "json"
    ) -> Optional[str]:
        """
        Save an export file (CSV or JSON) to S3.

        Args:
            batch_id: The batch ID
            export_id: Unique export identifier
            content: Export content
            format_type: 'json' or 'csv'

        Returns:
            S3 key if successful
        """
        extension = "json" if format_type == "json" else "csv"
        content_type = "application/json" if format_type == "json" else "text/csv"
        s3_key = f"{batch_id}/exports/{export_id}.{extension}"

        if isinstance(content, str):
            content = content.encode("utf-8")

        try:
            self.client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=content,
                ContentType=content_type,
                ServerSideEncryption="AES256",
                Metadata={
                    "batch_id": batch_id,
                    "export_id": export_id,
                    "format": format_type,
                    "created_at": datetime.utcnow().isoformat()
                }
            )
            return s3_key
        except ClientError as e:
            print(f"Error saving export: {e}")
            return None

    def get_export_url(
        self,
        s3_key: str,
        expiration: int = 3600
    ) -> Optional[str]:
        """Generate a presigned URL for export download."""
        return self.get_resume_url(s3_key, expiration)

    def list_exports(self, batch_id: str) -> List[Dict[str, Any]]:
        """List all exports for a batch."""
        prefix = f"{batch_id}/exports/"

        try:
            response = self.client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )

            exports = []
            for obj in response.get("Contents", []):
                key = obj["Key"]
                filename = key.split("/")[-1]
                export_id = filename.rsplit(".", 1)[0]
                format_type = "json" if filename.endswith(".json") else "csv"

                exports.append({
                    "key": key,
                    "export_id": export_id,
                    "format": format_type,
                    "size": obj["Size"],
                    "created_at": obj["LastModified"].isoformat(),
                })
            return exports
        except ClientError as e:
            print(f"Error listing exports: {e}")
            return []

    # ==================== Batch Cleanup Operations ====================

    def delete_batch_files(self, batch_id: str) -> bool:
        """Delete all files associated with a batch."""
        prefix = f"{batch_id}/"

        try:
            # List all objects with the batch prefix
            response = self.client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )

            if "Contents" not in response:
                return True

            # Delete in batches of 1000 (S3 limit)
            objects_to_delete = [{"Key": obj["Key"]} for obj in response["Contents"]]

            if objects_to_delete:
                self.client.delete_objects(
                    Bucket=self.bucket_name,
                    Delete={"Objects": objects_to_delete}
                )

            return True
        except ClientError as e:
            print(f"Error deleting batch files: {e}")
            return False

    # ==================== Utility Methods ====================

    def get_file_info(self, s3_key: str) -> Optional[Dict[str, Any]]:
        """Get metadata about a file in S3."""
        try:
            response = self.client.head_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            return {
                "key": s3_key,
                "size": response["ContentLength"],
                "content_type": response["ContentType"],
                "last_modified": response["LastModified"].isoformat(),
                "metadata": response.get("Metadata", {})
            }
        except ClientError as e:
            print(f"Error getting file info: {e}")
            return None

    def copy_file(self, source_key: str, dest_key: str) -> bool:
        """Copy a file within the bucket."""
        try:
            self.client.copy_object(
                Bucket=self.bucket_name,
                CopySource={"Bucket": self.bucket_name, "Key": source_key},
                Key=dest_key
            )
            return True
        except ClientError as e:
            print(f"Error copying file: {e}")
            return False


# Singleton instance
_s3_client: Optional[S3Client] = None


def get_s3() -> S3Client:
    """Get the S3 client singleton."""
    global _s3_client
    if _s3_client is None:
        _s3_client = S3Client()
    return _s3_client


def is_valid_resume_format(filename: str) -> bool:
    """Check if a filename has a supported resume format."""
    ext = os.path.splitext(filename)[1].lower()
    return ext in SUPPORTED_FORMATS


def get_content_type(filename: str) -> str:
    """Get the content type for a filename."""
    ext = os.path.splitext(filename)[1].lower()
    return SUPPORTED_FORMATS.get(ext, "application/octet-stream")
