"""
Email Service for Polished Resume Ranking System.
Handles notification emails for batch completion, placements, etc.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import os
import json

# Try to import email libraries
try:
    import boto3
    from botocore.exceptions import ClientError
    HAS_SES = True
except ImportError:
    HAS_SES = False

# Configuration
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
FROM_EMAIL = os.getenv("FROM_EMAIL", "noreply@polished.io")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@polished.io")


class EmailTemplates:
    """Email template definitions."""

    @staticmethod
    def batch_completed(batch_name: str, total_resumes: int, top_candidates: List[Dict]) -> Dict[str, str]:
        """Template for batch processing completion."""
        top_list = "\n".join([
            f"  {i+1}. {c.get('name', 'Unknown')} - Score: {c.get('score', 0):.1f}"
            for i, c in enumerate(top_candidates[:5])
        ])

        return {
            "subject": f"Batch '{batch_name}' Processing Complete",
            "html": f"""
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h1 style="color: #0ea5e9;">Batch Processing Complete</h1>
                <p>Your batch <strong>{batch_name}</strong> has finished processing.</p>

                <div style="background: #f3f4f6; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="margin-top: 0;">Summary</h3>
                    <p><strong>Total Resumes:</strong> {total_resumes}</p>
                    <p><strong>Processing Status:</strong> Complete</p>
                </div>

                <h3>Top Candidates</h3>
                <pre style="background: #f9fafb; padding: 15px; border-radius: 8px;">{top_list}</pre>

                <p>
                    <a href="https://app.polished.io/batches" style="display: inline-block; background: #0ea5e9; color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px;">
                        View Full Rankings
                    </a>
                </p>

                <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">
                <p style="color: #6b7280; font-size: 12px;">
                    This email was sent by Polished Resume Ranking System.
                </p>
            </body>
            </html>
            """,
            "text": f"""
Batch Processing Complete

Your batch "{batch_name}" has finished processing.

Summary:
- Total Resumes: {total_resumes}
- Processing Status: Complete

Top Candidates:
{top_list}

View full rankings at: https://app.polished.io/batches
            """,
        }

    @staticmethod
    def placement_reported(placement: Dict[str, Any]) -> Dict[str, str]:
        """Template for placement report notification."""
        return {
            "subject": f"New Placement Reported: {placement.get('company_name')}",
            "html": f"""
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h1 style="color: #22c55e;">New Placement Reported</h1>

                <div style="background: #f0fdf4; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="margin-top: 0; color: #16a34a;">Placement Details</h3>
                    <p><strong>Company:</strong> {placement.get('company_name')}</p>
                    <p><strong>Position:</strong> {placement.get('position')}</p>
                    <p><strong>Candidate:</strong> {placement.get('candidate_name', 'Not specified')}</p>
                    <p><strong>Fee:</strong> ${placement.get('fee_amount', 250)}</p>
                </div>

                <p>This placement requires verification before the fee can be processed.</p>

                <p>
                    <a href="https://app.polished.io/placements/{placement.get('placement_id')}" style="display: inline-block; background: #22c55e; color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px;">
                        Verify Placement
                    </a>
                </p>

                <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">
                <p style="color: #6b7280; font-size: 12px;">
                    This email was sent by Polished Resume Ranking System.
                </p>
            </body>
            </html>
            """,
            "text": f"""
New Placement Reported

Company: {placement.get('company_name')}
Position: {placement.get('position')}
Candidate: {placement.get('candidate_name', 'Not specified')}
Fee: ${placement.get('fee_amount', 250)}

This placement requires verification before the fee can be processed.

Verify at: https://app.polished.io/placements/{placement.get('placement_id')}
            """,
        }

    @staticmethod
    def placement_verified(placement: Dict[str, Any]) -> Dict[str, str]:
        """Template for placement verification notification."""
        return {
            "subject": f"Placement Verified - ${placement.get('fee_amount', 250)} Payment Pending",
            "html": f"""
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h1 style="color: #22c55e;">Placement Verified!</h1>

                <p>Great news! Your placement has been verified.</p>

                <div style="background: #f0fdf4; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="margin-top: 0; color: #16a34a;">Payment Details</h3>
                    <p><strong>Amount:</strong> ${placement.get('fee_amount', 250)}</p>
                    <p><strong>Status:</strong> Pending Payment</p>
                    <p><strong>Company:</strong> {placement.get('company_name')}</p>
                    <p><strong>Candidate:</strong> {placement.get('candidate_name', 'Not specified')}</p>
                </div>

                <p>Payment will be processed within 5-7 business days.</p>

                <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">
                <p style="color: #6b7280; font-size: 12px;">
                    This email was sent by Polished Resume Ranking System.
                </p>
            </body>
            </html>
            """,
            "text": f"""
Placement Verified!

Great news! Your placement has been verified.

Payment Details:
- Amount: ${placement.get('fee_amount', 250)}
- Status: Pending Payment
- Company: {placement.get('company_name')}
- Candidate: {placement.get('candidate_name', 'Not specified')}

Payment will be processed within 5-7 business days.
            """,
        }


class EmailService:
    """Service for sending emails via AWS SES."""

    def __init__(self):
        self.enabled = HAS_SES and os.getenv("ENABLE_EMAIL", "").lower() == "true"
        if self.enabled:
            self.client = boto3.client("ses", region_name=AWS_REGION)
        else:
            self.client = None

    async def send_email(
        self,
        to_addresses: List[str],
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
    ) -> bool:
        """
        Send an email.

        Args:
            to_addresses: List of recipient email addresses
            subject: Email subject
            html_body: HTML content
            text_body: Plain text content (optional)

        Returns:
            True if sent successfully
        """
        if not self.enabled:
            print(f"[Email Service Disabled] Would send to {to_addresses}: {subject}")
            return True

        try:
            message = {
                "Subject": {"Data": subject, "Charset": "UTF-8"},
                "Body": {
                    "Html": {"Data": html_body, "Charset": "UTF-8"},
                },
            }

            if text_body:
                message["Body"]["Text"] = {"Data": text_body, "Charset": "UTF-8"}

            self.client.send_email(
                Source=FROM_EMAIL,
                Destination={"ToAddresses": to_addresses},
                Message=message,
            )
            return True

        except ClientError as e:
            print(f"Error sending email: {e}")
            return False

    async def send_template(
        self,
        to_addresses: List[str],
        template: Dict[str, str],
    ) -> bool:
        """Send email using a template."""
        return await self.send_email(
            to_addresses=to_addresses,
            subject=template["subject"],
            html_body=template["html"],
            text_body=template.get("text"),
        )

    async def notify_batch_completed(
        self,
        email: str,
        batch_name: str,
        total_resumes: int,
        top_candidates: List[Dict],
    ) -> bool:
        """Send batch completion notification."""
        template = EmailTemplates.batch_completed(batch_name, total_resumes, top_candidates)
        return await self.send_template([email], template)

    async def notify_placement_reported(
        self,
        placement: Dict[str, Any],
    ) -> bool:
        """Send placement report notification to admin."""
        template = EmailTemplates.placement_reported(placement)
        return await self.send_template([ADMIN_EMAIL], template)

    async def notify_placement_verified(
        self,
        email: str,
        placement: Dict[str, Any],
    ) -> bool:
        """Send placement verification notification."""
        template = EmailTemplates.placement_verified(placement)
        return await self.send_template([email], template)


# Singleton instance
_email_service: Optional[EmailService] = None


def get_email_service() -> EmailService:
    """Get the email service singleton."""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service
