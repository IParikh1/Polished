"""
Pytest configuration and fixtures for Polished tests.
"""

import pytest
import asyncio
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport

# Set up event loop for async tests
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_resume_text() -> str:
    """Sample resume text for testing."""
    return """
John Smith
john.smith@email.com | (555) 123-4567 | San Francisco, CA | linkedin.com/in/johnsmith

PROFESSIONAL SUMMARY
Results-driven Sales Development Representative with 2 years of experience in B2B SaaS sales.
Consistently exceeded quota by 120% while building strong pipeline for the sales team.
Expert in Salesforce, Outreach, and LinkedIn Sales Navigator.

EXPERIENCE

Sales Development Representative | TechCorp Inc. | San Francisco, CA | Jan 2023 - Present
• Exceeded monthly meeting quota by 125%, booking 18+ qualified meetings per month
• Generated $2.4M in qualified pipeline for AE team through outbound prospecting
• Executed 80+ cold calls and 100+ personalized emails daily
• Achieved #2 ranking out of 12 SDRs in Q3 2024
• Mastered MEDDIC qualification framework for enterprise prospects

Business Development Representative | StartupXYZ | Remote | Jun 2022 - Dec 2022
• Ramped to full quota within 45 days (company average: 90 days)
• Booked 15 qualified meetings per month, achieving 110% of quota
• Developed multi-channel outreach sequences using Outreach.io
• Collaborated with marketing on lead scoring optimization

EDUCATION
Bachelor of Business Administration | University of California, Berkeley | 2022
Concentration in Marketing | GPA: 3.6

SKILLS
Sales Tools: Salesforce, Outreach, Salesloft, LinkedIn Sales Navigator, ZoomInfo, Gong
Methodologies: MEDDIC, BANT, Challenger Sale
Languages: English (native), Spanish (conversational)
"""


@pytest.fixture
def sample_sdr_resume() -> str:
    """Sample SDR resume for testing."""
    return """
Sarah Johnson
sarah.j@email.com | 415-555-0199

SDR at CloudTech Solutions
• 115% quota attainment average over 6 months
• 20 meetings booked per month
• Used Salesforce and Outreach daily
• Generated 50+ SQLs per quarter

Previous: Customer Service at Retail Co.
• Handled 100+ customer inquiries daily
• 95% customer satisfaction rating

Education: BA Communications, State University 2023
Skills: Cold calling, email sequences, CRM, prospecting
"""


@pytest.fixture
def sample_ae_resume() -> str:
    """Sample Account Executive resume for testing."""
    return """
Michael Chen
mchen@email.com | San Francisco

Senior Account Executive | Enterprise SaaS Corp | 2020-Present
• Closed $3.2M in ARR at 118% quota attainment
• Average deal size: $85K ACV
• 32% win rate on qualified opportunities
• Managed 6-month enterprise sales cycles
• Negotiated with C-suite executives at Fortune 500 companies

Account Executive | Growth StartupCo | 2018-2020
• $1.8M closed in first full year (125% of quota)
• 45 deals closed, averaging $40K ACV
• Self-sourced 40% of pipeline through referrals
• Shortened average sales cycle from 60 to 42 days

Education: MBA, Stanford GSB 2018
Certifications: Salesforce Certified, MEDDPICC trained
"""


@pytest.fixture
def sample_job_description() -> str:
    """Sample job description for testing."""
    return """
Account Executive - Mid-Market

We're looking for a driven Account Executive to join our growing sales team.

Requirements:
- 3+ years of B2B SaaS sales experience
- Track record of exceeding quota
- Experience with Salesforce and sales engagement tools
- Strong discovery and demo skills
- Experience with MEDDIC or similar methodology

Nice to have:
- Experience selling to mid-market companies
- Background in HR tech or similar vertical
- MBA or equivalent experience

Compensation: $150K OTE (50/50 split)
"""


@pytest.fixture
def mock_batch_data() -> dict:
    """Mock batch data for testing."""
    return {
        "batch_id": "batch-test123",
        "name": "Test Batch",
        "status": "pending",
        "total_resumes": 0,
        "processed_resumes": 0,
        "created_at": "2025-01-22T00:00:00",
        "updated_at": "2025-01-22T00:00:00",
        "job_description": None,
        "premium_features": [],
        "settings": {},
    }
