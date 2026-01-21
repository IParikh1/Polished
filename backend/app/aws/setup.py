"""
AWS Infrastructure Setup Script for Polished Resume Ranking System.
Creates DynamoDB tables and S3 bucket with proper configuration.
"""

import boto3
from botocore.exceptions import ClientError
import os
import time
from typing import Dict, Any

# AWS Configuration
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "polished-batches-us-east-1")

# Table names
BATCHES_TABLE = "polished-batches"
BATCH_RESUMES_TABLE = "polished-batch-resumes"
PLACEMENTS_TABLE = "polished-placements"


def get_dynamodb_client():
    """Get DynamoDB client."""
    return boto3.client("dynamodb", region_name=AWS_REGION)


def get_s3_client():
    """Get S3 client."""
    return boto3.client("s3", region_name=AWS_REGION)


def create_batches_table(client) -> bool:
    """
    Create the polished-batches table for batch metadata.

    Schema:
    - batch_id (PK): Unique batch identifier
    - user_id: User who created the batch (for GSI)
    - name: Batch name
    - status: pending | processing | completed | failed
    - total_resumes: Count of resumes
    - processed_resumes: Count of processed resumes
    - created_at: ISO timestamp
    - updated_at: ISO timestamp
    - job_description: Optional JD text for matching
    - premium_features: List of enabled premium features
    - settings: Batch-specific settings
    """
    try:
        client.create_table(
            TableName=BATCHES_TABLE,
            KeySchema=[
                {"AttributeName": "batch_id", "KeyType": "HASH"}
            ],
            AttributeDefinitions=[
                {"AttributeName": "batch_id", "AttributeType": "S"},
                {"AttributeName": "user_id", "AttributeType": "S"},
                {"AttributeName": "created_at", "AttributeType": "S"}
            ],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "user-index",
                    "KeySchema": [
                        {"AttributeName": "user_id", "KeyType": "HASH"},
                        {"AttributeName": "created_at", "KeyType": "RANGE"}
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                    "ProvisionedThroughput": {
                        "ReadCapacityUnits": 5,
                        "WriteCapacityUnits": 5
                    }
                }
            ],
            ProvisionedThroughput={
                "ReadCapacityUnits": 10,
                "WriteCapacityUnits": 10
            },
            Tags=[
                {"Key": "Project", "Value": "Polished"},
                {"Key": "Environment", "Value": os.getenv("ENVIRONMENT", "development")}
            ]
        )
        print(f"Created table: {BATCHES_TABLE}")
        return True
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceInUseException":
            print(f"Table {BATCHES_TABLE} already exists")
            return True
        print(f"Error creating {BATCHES_TABLE}: {e}")
        return False


def create_batch_resumes_table(client) -> bool:
    """
    Create the polished-batch-resumes table for resume data.

    Schema:
    - batch_id (PK): Parent batch identifier
    - resume_id (SK): Unique resume identifier
    - filename: Original filename
    - s3_key: S3 storage path
    - status: pending | processing | scored | failed
    - scores: Map of scoring categories
    - overall_score: Aggregated score (for GSI)
    - rank: Position in batch ranking
    - extracted_data: Parsed resume content
    - jd_match_score: JD matching score (premium)
    - deep_analysis: LLM analysis results (premium)
    """
    try:
        client.create_table(
            TableName=BATCH_RESUMES_TABLE,
            KeySchema=[
                {"AttributeName": "batch_id", "KeyType": "HASH"},
                {"AttributeName": "resume_id", "KeyType": "RANGE"}
            ],
            AttributeDefinitions=[
                {"AttributeName": "batch_id", "AttributeType": "S"},
                {"AttributeName": "resume_id", "AttributeType": "S"},
                {"AttributeName": "overall_score", "AttributeType": "N"}
            ],
            LocalSecondaryIndexes=[
                {
                    "IndexName": "score-index",
                    "KeySchema": [
                        {"AttributeName": "batch_id", "KeyType": "HASH"},
                        {"AttributeName": "overall_score", "KeyType": "RANGE"}
                    ],
                    "Projection": {"ProjectionType": "ALL"}
                }
            ],
            ProvisionedThroughput={
                "ReadCapacityUnits": 20,
                "WriteCapacityUnits": 20
            },
            Tags=[
                {"Key": "Project", "Value": "Polished"},
                {"Key": "Environment", "Value": os.getenv("ENVIRONMENT", "development")}
            ]
        )
        print(f"Created table: {BATCH_RESUMES_TABLE}")
        return True
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceInUseException":
            print(f"Table {BATCH_RESUMES_TABLE} already exists")
            return True
        print(f"Error creating {BATCH_RESUMES_TABLE}: {e}")
        return False


def create_placements_table(client) -> bool:
    """
    Create the polished-placements table for revenue tracking.

    Schema:
    - placement_id (PK): Unique placement identifier
    - batch_id: Source batch (for GSI)
    - resume_id: Placed resume
    - company_name: Hiring company
    - position: Job title
    - candidate_name: Placed candidate
    - placement_date: When placement occurred
    - reported_at: When reported
    - verification_status: pending | verified | disputed
    - fee_amount: Revenue amount ($250 default)
    - fee_paid: Boolean
    - verification_details: Verification metadata
    """
    try:
        client.create_table(
            TableName=PLACEMENTS_TABLE,
            KeySchema=[
                {"AttributeName": "placement_id", "KeyType": "HASH"}
            ],
            AttributeDefinitions=[
                {"AttributeName": "placement_id", "AttributeType": "S"},
                {"AttributeName": "batch_id", "AttributeType": "S"},
                {"AttributeName": "verification_status", "AttributeType": "S"},
                {"AttributeName": "reported_at", "AttributeType": "S"}
            ],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "batch-index",
                    "KeySchema": [
                        {"AttributeName": "batch_id", "KeyType": "HASH"},
                        {"AttributeName": "reported_at", "KeyType": "RANGE"}
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                    "ProvisionedThroughput": {
                        "ReadCapacityUnits": 5,
                        "WriteCapacityUnits": 5
                    }
                },
                {
                    "IndexName": "status-index",
                    "KeySchema": [
                        {"AttributeName": "verification_status", "KeyType": "HASH"},
                        {"AttributeName": "reported_at", "KeyType": "RANGE"}
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                    "ProvisionedThroughput": {
                        "ReadCapacityUnits": 5,
                        "WriteCapacityUnits": 5
                    }
                }
            ],
            ProvisionedThroughput={
                "ReadCapacityUnits": 10,
                "WriteCapacityUnits": 10
            },
            Tags=[
                {"Key": "Project", "Value": "Polished"},
                {"Key": "Environment", "Value": os.getenv("ENVIRONMENT", "development")}
            ]
        )
        print(f"Created table: {PLACEMENTS_TABLE}")
        return True
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceInUseException":
            print(f"Table {PLACEMENTS_TABLE} already exists")
            return True
        print(f"Error creating {PLACEMENTS_TABLE}: {e}")
        return False


def create_s3_bucket(client) -> bool:
    """
    Create S3 bucket with proper configuration.

    Structure:
    s3://polished-batches-us-east-1/
    ├── {batch_id}/
    │   ├── resumes/
    │   │   └── {resume_id}/
    │   │       └── {filename}
    │   ├── exports/
    │   │   └── {export_id}.{json|csv}
    │   └── metadata.json
    """
    try:
        # Check if bucket exists
        try:
            client.head_bucket(Bucket=BUCKET_NAME)
            print(f"Bucket {BUCKET_NAME} already exists")
            return True
        except ClientError as e:
            if e.response["Error"]["Code"] != "404":
                raise

        # Create bucket
        if AWS_REGION == "us-east-1":
            client.create_bucket(Bucket=BUCKET_NAME)
        else:
            client.create_bucket(
                Bucket=BUCKET_NAME,
                CreateBucketConfiguration={"LocationConstraint": AWS_REGION}
            )

        # Wait for bucket to be ready
        time.sleep(2)

        # Enable versioning
        client.put_bucket_versioning(
            Bucket=BUCKET_NAME,
            VersioningConfiguration={"Status": "Enabled"}
        )

        # Set lifecycle policy
        client.put_bucket_lifecycle_configuration(
            Bucket=BUCKET_NAME,
            LifecycleConfiguration={
                "Rules": [
                    {
                        "ID": "DeleteOldVersions",
                        "Status": "Enabled",
                        "NoncurrentVersionExpiration": {"NoncurrentDays": 30},
                        "Filter": {"Prefix": ""}
                    },
                    {
                        "ID": "DeleteOldExports",
                        "Status": "Enabled",
                        "Expiration": {"Days": 90},
                        "Filter": {"Prefix": "exports/"}
                    }
                ]
            }
        )

        # Block public access
        client.put_public_access_block(
            Bucket=BUCKET_NAME,
            PublicAccessBlockConfiguration={
                "BlockPublicAcls": True,
                "IgnorePublicAcls": True,
                "BlockPublicPolicy": True,
                "RestrictPublicBuckets": True
            }
        )

        # Enable server-side encryption
        client.put_bucket_encryption(
            Bucket=BUCKET_NAME,
            ServerSideEncryptionConfiguration={
                "Rules": [
                    {
                        "ApplyServerSideEncryptionByDefault": {
                            "SSEAlgorithm": "AES256"
                        }
                    }
                ]
            }
        )

        # Add CORS configuration for frontend uploads
        client.put_bucket_cors(
            Bucket=BUCKET_NAME,
            CORSConfiguration={
                "CORSRules": [
                    {
                        "AllowedHeaders": ["*"],
                        "AllowedMethods": ["GET", "PUT", "POST", "DELETE", "HEAD"],
                        "AllowedOrigins": ["http://localhost:3000", "http://localhost:5173"],
                        "ExposeHeaders": ["ETag"],
                        "MaxAgeSeconds": 3000
                    }
                ]
            }
        )

        # Add tags
        client.put_bucket_tagging(
            Bucket=BUCKET_NAME,
            Tagging={
                "TagSet": [
                    {"Key": "Project", "Value": "Polished"},
                    {"Key": "Environment", "Value": os.getenv("ENVIRONMENT", "development")}
                ]
            }
        )

        print(f"Created bucket: {BUCKET_NAME}")
        return True

    except ClientError as e:
        print(f"Error creating bucket: {e}")
        return False


def wait_for_table_active(client, table_name: str, timeout: int = 300) -> bool:
    """Wait for a DynamoDB table to become active."""
    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            response = client.describe_table(TableName=table_name)
            status = response["Table"]["TableStatus"]

            if status == "ACTIVE":
                return True
            elif status in ["CREATING", "UPDATING"]:
                time.sleep(5)
            else:
                print(f"Table {table_name} in unexpected state: {status}")
                return False
        except ClientError as e:
            print(f"Error checking table status: {e}")
            return False

    print(f"Timeout waiting for table {table_name}")
    return False


def setup_infrastructure() -> Dict[str, bool]:
    """
    Set up all AWS infrastructure for Polished.

    Returns:
        Dictionary with setup results for each component
    """
    results = {
        "batches_table": False,
        "batch_resumes_table": False,
        "placements_table": False,
        "s3_bucket": False
    }

    print("=" * 50)
    print("Setting up Polished AWS Infrastructure")
    print(f"Region: {AWS_REGION}")
    print("=" * 50)

    # Create DynamoDB tables
    dynamodb = get_dynamodb_client()

    print("\n[1/4] Creating batches table...")
    results["batches_table"] = create_batches_table(dynamodb)

    print("\n[2/4] Creating batch resumes table...")
    results["batch_resumes_table"] = create_batch_resumes_table(dynamodb)

    print("\n[3/4] Creating placements table...")
    results["placements_table"] = create_placements_table(dynamodb)

    # Wait for tables to be active
    print("\nWaiting for tables to be active...")
    for table_name in [BATCHES_TABLE, BATCH_RESUMES_TABLE, PLACEMENTS_TABLE]:
        if wait_for_table_active(dynamodb, table_name):
            print(f"  {table_name}: ACTIVE")
        else:
            print(f"  {table_name}: FAILED")

    # Create S3 bucket
    print("\n[4/4] Creating S3 bucket...")
    s3 = get_s3_client()
    results["s3_bucket"] = create_s3_bucket(s3)

    # Summary
    print("\n" + "=" * 50)
    print("Setup Summary")
    print("=" * 50)
    for component, success in results.items():
        status = "SUCCESS" if success else "FAILED"
        print(f"  {component}: {status}")

    all_success = all(results.values())
    print("\n" + ("Setup completed successfully!" if all_success else "Setup completed with errors."))

    return results


def teardown_infrastructure() -> Dict[str, bool]:
    """
    Tear down all AWS infrastructure for Polished.
    USE WITH CAUTION - This deletes all data!

    Returns:
        Dictionary with teardown results for each component
    """
    results = {
        "batches_table": False,
        "batch_resumes_table": False,
        "placements_table": False,
        "s3_bucket": False
    }

    print("=" * 50)
    print("TEARING DOWN Polished AWS Infrastructure")
    print("WARNING: This will delete all data!")
    print("=" * 50)

    dynamodb = get_dynamodb_client()
    s3 = get_s3_client()

    # Delete DynamoDB tables
    for table_name in [BATCHES_TABLE, BATCH_RESUMES_TABLE, PLACEMENTS_TABLE]:
        try:
            dynamodb.delete_table(TableName=table_name)
            print(f"Deleted table: {table_name}")
            results[table_name.replace("polished-", "").replace("-", "_")] = True
        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                print(f"Table {table_name} does not exist")
                results[table_name.replace("polished-", "").replace("-", "_")] = True
            else:
                print(f"Error deleting {table_name}: {e}")

    # Delete S3 bucket (must empty first)
    try:
        # Delete all objects
        bucket = boto3.resource("s3").Bucket(BUCKET_NAME)
        bucket.objects.all().delete()
        bucket.object_versions.all().delete()

        # Delete bucket
        s3.delete_bucket(Bucket=BUCKET_NAME)
        print(f"Deleted bucket: {BUCKET_NAME}")
        results["s3_bucket"] = True
    except ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchBucket":
            print(f"Bucket {BUCKET_NAME} does not exist")
            results["s3_bucket"] = True
        else:
            print(f"Error deleting bucket: {e}")

    return results


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "teardown":
        confirmation = input("Type 'DELETE' to confirm teardown: ")
        if confirmation == "DELETE":
            teardown_infrastructure()
        else:
            print("Teardown cancelled")
    else:
        setup_infrastructure()
