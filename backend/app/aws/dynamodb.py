"""
DynamoDB client utilities for Polished Resume Ranking System.
Handles connections and operations for batch, resume, and placement tables.
"""

import boto3
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError
from typing import Dict, List, Optional, Any
from datetime import datetime
import os
import json
from decimal import Decimal

# AWS Configuration
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

# Table names
BATCHES_TABLE = "polished-batches"
BATCH_RESUMES_TABLE = "polished-batch-resumes"
PLACEMENTS_TABLE = "polished-placements"
USERS_TABLE = "polished-users"
USAGE_TABLE = "polished-usage"


class DecimalEncoder(json.JSONEncoder):
    """Helper class to convert Decimal to float for JSON serialization."""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


def convert_decimals(obj):
    """Recursively convert Decimal values to float in nested structures."""
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {k: convert_decimals(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_decimals(item) for item in obj]
    return obj


def get_dynamodb_resource():
    """Get DynamoDB resource with configured region."""
    return boto3.resource("dynamodb", region_name=AWS_REGION)


def get_dynamodb_client():
    """Get DynamoDB client with configured region."""
    return boto3.client("dynamodb", region_name=AWS_REGION)


class DynamoDBClient:
    """Client for DynamoDB operations."""

    def __init__(self):
        self.resource = get_dynamodb_resource()
        self.client = get_dynamodb_client()

    # ==================== Batch Operations ====================

    def create_batch(self, batch_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new batch record.

        Args:
            batch_data: Dictionary containing batch metadata
                - batch_id: Unique batch identifier
                - user_id: User who created the batch
                - name: Batch name
                - status: Current status (pending, processing, completed, failed)
                - total_resumes: Number of resumes in batch
                - created_at: ISO timestamp

        Returns:
            The created batch record
        """
        table = self.resource.Table(BATCHES_TABLE)

        item = {
            "batch_id": batch_data["batch_id"],
            "user_id": batch_data.get("user_id", "anonymous"),
            "name": batch_data.get("name", f"Batch {batch_data['batch_id'][:8]}"),
            "status": batch_data.get("status", "pending"),
            "total_resumes": batch_data.get("total_resumes", 0),
            "processed_resumes": batch_data.get("processed_resumes", 0),
            "created_at": batch_data.get("created_at", datetime.utcnow().isoformat()),
            "updated_at": datetime.utcnow().isoformat(),
            "job_description": batch_data.get("job_description"),
            "premium_features": batch_data.get("premium_features", []),
            "settings": batch_data.get("settings", {}),
        }

        table.put_item(Item=item)
        return item

    def get_batch(self, batch_id: str) -> Optional[Dict[str, Any]]:
        """Get a batch by ID."""
        table = self.resource.Table(BATCHES_TABLE)

        try:
            response = table.get_item(Key={"batch_id": batch_id})
            return response.get("Item")
        except ClientError as e:
            print(f"Error getting batch: {e}")
            return None

    def update_batch_status(
        self,
        batch_id: str,
        status: str,
        processed_resumes: Optional[int] = None
    ) -> bool:
        """Update batch status and optionally the processed count."""
        table = self.resource.Table(BATCHES_TABLE)

        update_expr = "SET #status = :status, updated_at = :updated_at"
        expr_values = {
            ":status": status,
            ":updated_at": datetime.utcnow().isoformat()
        }
        expr_names = {"#status": "status"}

        if processed_resumes is not None:
            update_expr += ", processed_resumes = :processed"
            expr_values[":processed"] = processed_resumes

        try:
            table.update_item(
                Key={"batch_id": batch_id},
                UpdateExpression=update_expr,
                ExpressionAttributeNames=expr_names,
                ExpressionAttributeValues=expr_values
            )
            return True
        except ClientError as e:
            print(f"Error updating batch: {e}")
            return False

    def list_batches(
        self,
        user_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """List batches, optionally filtered by user."""
        table = self.resource.Table(BATCHES_TABLE)

        try:
            if user_id:
                # Use GSI for user queries
                response = table.query(
                    IndexName="user-index",
                    KeyConditionExpression=Key("user_id").eq(user_id),
                    Limit=limit,
                    ScanIndexForward=False  # Most recent first
                )
            else:
                response = table.scan(Limit=limit)

            return response.get("Items", [])
        except ClientError as e:
            print(f"Error listing batches: {e}")
            return []

    def delete_batch(self, batch_id: str) -> bool:
        """Delete a batch and all associated resumes."""
        # First delete all resumes in the batch
        self.delete_batch_resumes(batch_id)

        # Then delete the batch itself
        table = self.resource.Table(BATCHES_TABLE)
        try:
            table.delete_item(Key={"batch_id": batch_id})
            return True
        except ClientError as e:
            print(f"Error deleting batch: {e}")
            return False

    # ==================== Resume Operations ====================

    def add_resume_to_batch(self, resume_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add a resume to a batch.

        Args:
            resume_data: Dictionary containing resume data
                - batch_id: Parent batch ID
                - resume_id: Unique resume identifier
                - filename: Original filename
                - s3_key: S3 storage key
                - status: Processing status
                - scores: Scoring results (optional)
        """
        table = self.resource.Table(BATCH_RESUMES_TABLE)

        item = {
            "batch_id": resume_data["batch_id"],
            "resume_id": resume_data["resume_id"],
            "filename": resume_data.get("filename", "unknown"),
            "s3_key": resume_data.get("s3_key"),
            "status": resume_data.get("status", "pending"),
            "target_role": resume_data.get("target_role"),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "scores": resume_data.get("scores", {}),
            "overall_score": resume_data.get("overall_score"),
            "rank": resume_data.get("rank"),
            "extracted_data": resume_data.get("extracted_data", {}),
            "jd_match_score": resume_data.get("jd_match_score"),
            "deep_analysis": resume_data.get("deep_analysis"),
        }

        table.put_item(Item=item)
        return item

    def get_resume(self, batch_id: str, resume_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific resume from a batch."""
        table = self.resource.Table(BATCH_RESUMES_TABLE)

        try:
            response = table.get_item(
                Key={"batch_id": batch_id, "resume_id": resume_id}
            )
            item = response.get("Item")
            # Convert Decimal values to float for API compatibility
            return convert_decimals(item) if item else None
        except ClientError as e:
            print(f"Error getting resume: {e}")
            return None

    def get_batch_resumes(
        self,
        batch_id: str,
        sort_by_score: bool = True
    ) -> List[Dict[str, Any]]:
        """Get all resumes in a batch, optionally sorted by score."""
        table = self.resource.Table(BATCH_RESUMES_TABLE)

        try:
            response = table.query(
                KeyConditionExpression=Key("batch_id").eq(batch_id)
            )
            resumes = response.get("Items", [])

            # Convert Decimal values to float for API compatibility
            resumes = [convert_decimals(r) for r in resumes]

            if sort_by_score:
                resumes.sort(
                    key=lambda x: float(x.get("overall_score", 0) or 0),
                    reverse=True
                )

            return resumes
        except ClientError as e:
            print(f"Error getting batch resumes: {e}")
            return []

    def update_resume_scores(
        self,
        batch_id: str,
        resume_id: str,
        scores: Dict[str, float],
        overall_score: float,
        rank: Optional[int] = None
    ) -> bool:
        """Update resume scores and ranking."""
        table = self.resource.Table(BATCH_RESUMES_TABLE)

        # Convert float values in scores dict to Decimal for DynamoDB
        scores_decimal = {k: Decimal(str(v)) for k, v in scores.items()}

        update_expr = """
            SET scores = :scores,
                overall_score = :overall,
                updated_at = :updated,
                #status = :status
        """
        expr_values = {
            ":scores": scores_decimal,
            ":overall": Decimal(str(overall_score)),
            ":updated": datetime.utcnow().isoformat(),
            ":status": "scored"
        }
        expr_names = {"#status": "status"}

        if rank is not None:
            update_expr += ", #rank = :rank"
            expr_values[":rank"] = rank
            expr_names["#rank"] = "rank"

        try:
            table.update_item(
                Key={"batch_id": batch_id, "resume_id": resume_id},
                UpdateExpression=update_expr,
                ExpressionAttributeNames=expr_names,
                ExpressionAttributeValues=expr_values
            )
            return True
        except ClientError as e:
            print(f"Error updating resume scores: {e}")
            return False

    def update_resume_jd_match(
        self,
        batch_id: str,
        resume_id: str,
        jd_match_score: float,
        match_details: Optional[Dict] = None
    ) -> bool:
        """Update JD matching score for a resume."""
        table = self.resource.Table(BATCH_RESUMES_TABLE)

        update_expr = "SET jd_match_score = :score, updated_at = :updated"
        expr_values = {
            ":score": Decimal(str(jd_match_score)),
            ":updated": datetime.utcnow().isoformat()
        }

        if match_details:
            update_expr += ", jd_match_details = :details"
            expr_values[":details"] = match_details

        try:
            table.update_item(
                Key={"batch_id": batch_id, "resume_id": resume_id},
                UpdateExpression=update_expr,
                ExpressionAttributeValues=expr_values
            )
            return True
        except ClientError as e:
            print(f"Error updating JD match: {e}")
            return False

    def update_resume_deep_analysis(
        self,
        batch_id: str,
        resume_id: str,
        analysis: Dict[str, Any]
    ) -> bool:
        """Store deep LLM analysis results for a resume."""
        table = self.resource.Table(BATCH_RESUMES_TABLE)

        try:
            table.update_item(
                Key={"batch_id": batch_id, "resume_id": resume_id},
                UpdateExpression="SET deep_analysis = :analysis, updated_at = :updated",
                ExpressionAttributeValues={
                    ":analysis": analysis,
                    ":updated": datetime.utcnow().isoformat()
                }
            )
            return True
        except ClientError as e:
            print(f"Error updating deep analysis: {e}")
            return False

    def delete_batch_resumes(self, batch_id: str) -> bool:
        """Delete all resumes in a batch."""
        table = self.resource.Table(BATCH_RESUMES_TABLE)

        try:
            resumes = self.get_batch_resumes(batch_id, sort_by_score=False)

            with table.batch_writer() as batch:
                for resume in resumes:
                    batch.delete_item(
                        Key={
                            "batch_id": batch_id,
                            "resume_id": resume["resume_id"]
                        }
                    )
            return True
        except ClientError as e:
            print(f"Error deleting batch resumes: {e}")
            return False

    # ==================== Placement Operations ====================

    def create_placement(self, placement_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a placement record for revenue tracking.

        Args:
            placement_data: Dictionary containing:
                - placement_id: Unique identifier
                - batch_id: Source batch
                - resume_id: Placed resume
                - company_name: Hiring company
                - position: Job title
                - candidate_name: Name of placed candidate
                - placement_date: When placement occurred
                - verification_status: pending, verified, disputed
                - fee_amount: Revenue amount (default $250)
        """
        table = self.resource.Table(PLACEMENTS_TABLE)

        item = {
            "placement_id": placement_data["placement_id"],
            "batch_id": placement_data["batch_id"],
            "resume_id": placement_data["resume_id"],
            "company_name": placement_data["company_name"],
            "position": placement_data["position"],
            "candidate_name": placement_data.get("candidate_name", "Unknown"),
            "placement_date": placement_data.get(
                "placement_date",
                datetime.utcnow().isoformat()
            ),
            "reported_at": datetime.utcnow().isoformat(),
            "verification_status": placement_data.get("verification_status", "pending"),
            "fee_amount": Decimal(str(placement_data.get("fee_amount", 250))),
            "fee_paid": placement_data.get("fee_paid", False),
            "verification_details": placement_data.get("verification_details", {}),
            "notes": placement_data.get("notes", ""),
        }

        table.put_item(Item=item)
        return item

    def get_placement(self, placement_id: str) -> Optional[Dict[str, Any]]:
        """Get a placement by ID."""
        table = self.resource.Table(PLACEMENTS_TABLE)

        try:
            response = table.get_item(Key={"placement_id": placement_id})
            return response.get("Item")
        except ClientError as e:
            print(f"Error getting placement: {e}")
            return None

    def list_placements(
        self,
        batch_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """List placements with optional filters."""
        table = self.resource.Table(PLACEMENTS_TABLE)

        try:
            if batch_id:
                response = table.query(
                    IndexName="batch-index",
                    KeyConditionExpression=Key("batch_id").eq(batch_id),
                    Limit=limit
                )
            else:
                scan_kwargs = {"Limit": limit}
                if status:
                    scan_kwargs["FilterExpression"] = Attr("verification_status").eq(status)
                response = table.scan(**scan_kwargs)

            return response.get("Items", [])
        except ClientError as e:
            print(f"Error listing placements: {e}")
            return []

    def update_placement_status(
        self,
        placement_id: str,
        status: str,
        verification_details: Optional[Dict] = None
    ) -> bool:
        """Update placement verification status."""
        table = self.resource.Table(PLACEMENTS_TABLE)

        update_expr = "SET verification_status = :status, updated_at = :updated"
        expr_values = {
            ":status": status,
            ":updated": datetime.utcnow().isoformat()
        }

        if verification_details:
            update_expr += ", verification_details = :details"
            expr_values[":details"] = verification_details

        try:
            table.update_item(
                Key={"placement_id": placement_id},
                UpdateExpression=update_expr,
                ExpressionAttributeValues=expr_values
            )
            return True
        except ClientError as e:
            print(f"Error updating placement status: {e}")
            return False

    def mark_placement_paid(self, placement_id: str) -> bool:
        """Mark a placement fee as paid."""
        table = self.resource.Table(PLACEMENTS_TABLE)

        try:
            table.update_item(
                Key={"placement_id": placement_id},
                UpdateExpression="SET fee_paid = :paid, paid_at = :paid_at",
                ExpressionAttributeValues={
                    ":paid": True,
                    ":paid_at": datetime.utcnow().isoformat()
                }
            )
            return True
        except ClientError as e:
            print(f"Error marking placement paid: {e}")
            return False

    def get_placement_stats(self) -> Dict[str, Any]:
        """Get aggregated placement statistics."""
        table = self.resource.Table(PLACEMENTS_TABLE)

        try:
            response = table.scan()
            placements = response.get("Items", [])

            total_placements = len(placements)
            verified = sum(1 for p in placements if p.get("verification_status") == "verified")
            pending = sum(1 for p in placements if p.get("verification_status") == "pending")
            disputed = sum(1 for p in placements if p.get("verification_status") == "disputed")

            total_revenue = sum(
                float(p.get("fee_amount", 0))
                for p in placements
                if p.get("fee_paid")
            )
            pending_revenue = sum(
                float(p.get("fee_amount", 0))
                for p in placements
                if p.get("verification_status") == "verified" and not p.get("fee_paid")
            )

            return {
                "total_placements": total_placements,
                "verified": verified,
                "pending": pending,
                "disputed": disputed,
                "total_revenue": total_revenue,
                "pending_revenue": pending_revenue
            }
        except ClientError as e:
            print(f"Error getting placement stats: {e}")
            return {}

    # ==================== User Operations ====================

    def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create or update a user record.

        Args:
            user_data: Dictionary containing user data
                - user_id: Clerk user ID (PK)
                - email: User's email
                - name: User's full name
                - subscription_tier: free, pro, enterprise
                - stripe_customer_id: Stripe customer ID
                - stripe_subscription_id: Stripe subscription ID
                - subscription_status: active, canceled, past_due
        """
        table = self.resource.Table(USERS_TABLE)

        item = {
            "user_id": user_data["user_id"],
            "email": user_data.get("email", ""),
            "name": user_data.get("name", ""),
            "subscription_tier": user_data.get("subscription_tier", "free"),
            "stripe_customer_id": user_data.get("stripe_customer_id"),
            "stripe_subscription_id": user_data.get("stripe_subscription_id"),
            "subscription_status": user_data.get("subscription_status"),
            "created_at": user_data.get("created_at", datetime.utcnow().isoformat()),
            "updated_at": datetime.utcnow().isoformat(),
        }

        # Remove None values
        item = {k: v for k, v in item.items() if v is not None}

        table.put_item(Item=item)
        return item

    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get a user by their Clerk user ID."""
        table = self.resource.Table(USERS_TABLE)

        try:
            response = table.get_item(Key={"user_id": user_id})
            return response.get("Item")
        except ClientError as e:
            print(f"Error getting user: {e}")
            return None

    def get_user_by_stripe_customer(self, stripe_customer_id: str) -> Optional[Dict[str, Any]]:
        """Get a user by their Stripe customer ID."""
        table = self.resource.Table(USERS_TABLE)

        try:
            response = table.query(
                IndexName="stripe-customer-index",
                KeyConditionExpression=Key("stripe_customer_id").eq(stripe_customer_id)
            )
            items = response.get("Items", [])
            return items[0] if items else None
        except ClientError as e:
            print(f"Error getting user by Stripe customer: {e}")
            return None

    def update_user(self, user_id: str, updates: Dict[str, Any]) -> bool:
        """Update user fields."""
        table = self.resource.Table(USERS_TABLE)

        # Build update expression dynamically
        update_parts = []
        expr_values = {":updated": datetime.utcnow().isoformat()}

        for key, value in updates.items():
            if key != "user_id":  # Don't update the primary key
                update_parts.append(f"{key} = :{key}")
                expr_values[f":{key}"] = value

        if not update_parts:
            return True  # Nothing to update

        update_parts.append("updated_at = :updated")
        update_expr = "SET " + ", ".join(update_parts)

        try:
            table.update_item(
                Key={"user_id": user_id},
                UpdateExpression=update_expr,
                ExpressionAttributeValues=expr_values
            )
            return True
        except ClientError as e:
            print(f"Error updating user: {e}")
            return False

    def update_user_subscription(
        self,
        user_id: str,
        subscription_tier: str,
        stripe_customer_id: Optional[str] = None,
        stripe_subscription_id: Optional[str] = None,
        subscription_status: Optional[str] = None
    ) -> bool:
        """Update user subscription details."""
        table = self.resource.Table(USERS_TABLE)

        update_expr = "SET subscription_tier = :tier, updated_at = :updated"
        expr_values = {
            ":tier": subscription_tier,
            ":updated": datetime.utcnow().isoformat()
        }

        if stripe_customer_id:
            update_expr += ", stripe_customer_id = :customer_id"
            expr_values[":customer_id"] = stripe_customer_id

        if stripe_subscription_id:
            update_expr += ", stripe_subscription_id = :sub_id"
            expr_values[":sub_id"] = stripe_subscription_id

        if subscription_status:
            update_expr += ", subscription_status = :status"
            expr_values[":status"] = subscription_status

        try:
            table.update_item(
                Key={"user_id": user_id},
                UpdateExpression=update_expr,
                ExpressionAttributeValues=expr_values
            )
            return True
        except ClientError as e:
            print(f"Error updating user subscription: {e}")
            return False

    def get_or_create_user(
        self,
        user_id: str,
        email: str,
        name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get existing user or create a new one with default free tier."""
        user = self.get_user(user_id)
        if user:
            return user

        # Create new user with free tier
        return self.create_user({
            "user_id": user_id,
            "email": email,
            "name": name or "",
            "subscription_tier": "free",
        })

    # ==================== Admin Operations ====================

    def set_user_admin(self, user_id: str, is_admin: bool) -> bool:
        """Set or remove admin status for a user."""
        table = self.resource.Table(USERS_TABLE)

        try:
            table.update_item(
                Key={"user_id": user_id},
                UpdateExpression="SET is_admin = :admin, updated_at = :updated",
                ExpressionAttributeValues={
                    ":admin": is_admin,
                    ":updated": datetime.utcnow().isoformat()
                }
            )
            return True
        except ClientError as e:
            print(f"Error updating user admin status: {e}")
            return False

    def is_user_admin(self, user_id: str) -> bool:
        """Check if a user is an admin."""
        user = self.get_user(user_id)
        if user:
            return user.get("is_admin", False)
        return False

    def list_all_users(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> tuple[List[Dict[str, Any]], int]:
        """List all users (admin only). Returns (users, total_count)."""
        table = self.resource.Table(USERS_TABLE)

        try:
            # Scan for all users
            response = table.scan()
            items = response.get("Items", [])

            # Handle pagination for large tables
            while "LastEvaluatedKey" in response:
                response = table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
                items.extend(response.get("Items", []))

            total = len(items)

            # Sort by created_at descending
            items.sort(key=lambda x: x.get("created_at", ""), reverse=True)

            # Apply pagination
            paginated = items[offset:offset + limit]

            return convert_decimals(paginated), total
        except ClientError as e:
            print(f"Error listing all users: {e}")
            return [], 0

    def get_admin_stats(self) -> Dict[str, Any]:
        """Get aggregate stats for admin dashboard."""
        users_table = self.resource.Table(USERS_TABLE)
        batches_table = self.resource.Table(BATCHES_TABLE)
        resumes_table = self.resource.Table(BATCH_RESUMES_TABLE)

        stats = {
            "total_users": 0,
            "users_by_tier": {"free": 0, "pro": 0, "enterprise": 0},
            "users_by_status": {},
            "total_batches": 0,
            "total_resumes": 0,
            "total_revenue": 0.0,
            "period": datetime.utcnow().strftime("%Y-%m"),
        }

        try:
            # Scan users
            response = users_table.scan()
            users = response.get("Items", [])
            while "LastEvaluatedKey" in response:
                response = users_table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
                users.extend(response.get("Items", []))

            stats["total_users"] = len(users)
            for user in users:
                tier = user.get("subscription_tier", "free")
                stats["users_by_tier"][tier] = stats["users_by_tier"].get(tier, 0) + 1

                status = user.get("subscription_status")
                if status:
                    stats["users_by_status"][status] = stats["users_by_status"].get(status, 0) + 1

            # Count batches
            response = batches_table.scan(Select="COUNT")
            stats["total_batches"] = response.get("Count", 0)

            # Count resumes
            response = resumes_table.scan(Select="COUNT")
            stats["total_resumes"] = response.get("Count", 0)

        except ClientError as e:
            print(f"Error getting admin stats: {e}")

        return stats

    # ==================== Usage Tracking Operations ====================

    def record_usage(
        self,
        user_id: str,
        usage_type: str,
        amount: int = 1
    ) -> bool:
        """
        Record usage for a user. Creates monthly aggregates.

        Args:
            user_id: User ID
            usage_type: One of: batches_created, resumes_processed, exports_count,
                       jd_matches, resume_writes, deep_analyses
            amount: Amount to increment
        """
        table = self.resource.Table(USAGE_TABLE)
        period = datetime.utcnow().strftime("%Y-%m")

        try:
            # Use atomic counter with update
            table.update_item(
                Key={
                    "user_id": user_id,
                    "period": period,
                },
                UpdateExpression=f"SET {usage_type} = if_not_exists({usage_type}, :zero) + :amt, updated_at = :updated",
                ExpressionAttributeValues={
                    ":amt": amount,
                    ":zero": 0,
                    ":updated": datetime.utcnow().isoformat(),
                }
            )
            return True
        except ClientError as e:
            print(f"Error recording usage: {e}")
            return False

    def get_user_usage(
        self,
        user_id: str,
        period: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Get usage for a user for a specific period (default: current month)."""
        table = self.resource.Table(USAGE_TABLE)
        if not period:
            period = datetime.utcnow().strftime("%Y-%m")

        try:
            response = table.get_item(
                Key={
                    "user_id": user_id,
                    "period": period,
                }
            )
            item = response.get("Item")
            if item:
                return convert_decimals(item)
            # Return default empty usage
            return {
                "user_id": user_id,
                "period": period,
                "batches_created": 0,
                "resumes_processed": 0,
                "exports_count": 0,
                "jd_matches": 0,
                "resume_writes": 0,
                "deep_analyses": 0,
            }
        except ClientError as e:
            print(f"Error getting user usage: {e}")
            return None

    def get_all_usage_for_period(
        self,
        period: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get usage for all users for a period."""
        table = self.resource.Table(USAGE_TABLE)
        if not period:
            period = datetime.utcnow().strftime("%Y-%m")

        try:
            response = table.query(
                IndexName="period-index",
                KeyConditionExpression=Key("period").eq(period)
            )
            return convert_decimals(response.get("Items", []))
        except ClientError as e:
            # If index doesn't exist, fall back to scan
            try:
                response = table.scan(
                    FilterExpression=Attr("period").eq(period)
                )
                return convert_decimals(response.get("Items", []))
            except ClientError as e2:
                print(f"Error getting all usage: {e2}")
                return []


# Singleton instance
_db_client: Optional[DynamoDBClient] = None


def get_db() -> DynamoDBClient:
    """Get the DynamoDB client singleton."""
    global _db_client
    if _db_client is None:
        _db_client = DynamoDBClient()
    return _db_client
