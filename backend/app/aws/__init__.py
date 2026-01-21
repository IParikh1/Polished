"""
AWS module for Polished Resume Ranking System.
Provides DynamoDB and S3 client utilities.
"""

from .dynamodb import (
    DynamoDBClient,
    get_db,
    BATCHES_TABLE,
    BATCH_RESUMES_TABLE,
    PLACEMENTS_TABLE,
)

from .s3 import (
    S3Client,
    get_s3,
    BUCKET_NAME,
    SUPPORTED_FORMATS,
    is_valid_resume_format,
    get_content_type,
)

from .setup import setup_infrastructure, teardown_infrastructure

__all__ = [
    # DynamoDB
    "DynamoDBClient",
    "get_db",
    "BATCHES_TABLE",
    "BATCH_RESUMES_TABLE",
    "PLACEMENTS_TABLE",
    # S3
    "S3Client",
    "get_s3",
    "BUCKET_NAME",
    "SUPPORTED_FORMATS",
    "is_valid_resume_format",
    "get_content_type",
    # Setup
    "setup_infrastructure",
    "teardown_infrastructure",
]
