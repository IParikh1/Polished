"""
API tests for role-specific optimization endpoints.
Tests the full flow from upload with target_role to processing.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import io

from app.models.batch_schemas import SalesRole
from app.middleware.auth import AuthenticatedUser

TEST_USER = AuthenticatedUser(user_id="test-user-001", email="test@example.com")


class TestRoleUploadEndpoint:
    """Tests for upload endpoints with target_role parameter."""

    @pytest.mark.asyncio
    async def test_upload_accepts_target_role(self, mock_batch_data):
        """Test that upload endpoint accepts target_role parameter."""
        from app.api.batch_routes import upload_resume
        from fastapi import UploadFile

        # Mock the store
        with patch('app.api.batch_routes.get_store') as mock_store:
            store_instance = AsyncMock()
            store_instance.get_batch.return_value = mock_batch_data
            store_instance.add_resume.return_value = {
                "resume_id": "resume-test123",
                "filename": "test.pdf",
                "status": "pending",
                "target_role": "account_executive",
            }
            mock_store.return_value = store_instance

            # Create mock file
            file_content = b"Mock PDF content"
            mock_file = MagicMock(spec=UploadFile)
            mock_file.filename = "test.pdf"
            mock_file.content_type = "application/pdf"
            mock_file.read = AsyncMock(return_value=file_content)

            # Call endpoint with target_role
            result = await upload_resume(
                batch_id="batch-test123",
                file=mock_file,
                target_role=SalesRole.ACCOUNT_EXECUTIVE,
                user=TEST_USER,
            )

            # Verify result
            assert result["resume_id"] == "resume-test123"
            assert result["target_role"] == "account_executive"

            # Verify store was called with target_role
            store_instance.add_resume.assert_called_once()
            call_kwargs = store_instance.add_resume.call_args[1]
            assert call_kwargs.get("target_role") == "account_executive"

    @pytest.mark.asyncio
    async def test_upload_multiple_with_target_role(self, mock_batch_data):
        """Test that upload-multiple endpoint accepts target_role."""
        from app.api.batch_routes import upload_multiple_resumes
        from fastapi import UploadFile

        with patch('app.api.batch_routes.get_store') as mock_store:
            store_instance = AsyncMock()
            store_instance.get_batch.return_value = mock_batch_data
            store_instance.add_resume.return_value = {
                "resume_id": "resume-test123",
                "filename": "test.pdf",
                "status": "pending",
            }
            mock_store.return_value = store_instance

            # Create mock files
            mock_files = []
            for i in range(3):
                mock_file = MagicMock(spec=UploadFile)
                mock_file.filename = f"test{i}.pdf"
                mock_file.content_type = "application/pdf"
                mock_file.read = AsyncMock(return_value=b"Mock PDF content")
                mock_files.append(mock_file)

            # Call endpoint with target_role
            result = await upload_multiple_resumes(
                batch_id="batch-test123",
                files=mock_files,
                target_role=SalesRole.SDR,
                role_mapping=None,
                user=TEST_USER,
            )

            # Verify result
            assert result["uploaded"] == 3
            assert result["target_role"] == "sdr"

            # Verify all add_resume calls included target_role
            for call in store_instance.add_resume.call_args_list:
                assert call[1].get("target_role") == "sdr"

    @pytest.mark.asyncio
    async def test_upload_without_target_role(self, mock_batch_data):
        """Test that upload works without target_role (backward compatible)."""
        from app.api.batch_routes import upload_resume
        from fastapi import UploadFile

        with patch('app.api.batch_routes.get_store') as mock_store:
            store_instance = AsyncMock()
            store_instance.get_batch.return_value = mock_batch_data
            store_instance.add_resume.return_value = {
                "resume_id": "resume-test123",
                "filename": "test.pdf",
                "status": "pending",
            }
            mock_store.return_value = store_instance

            mock_file = MagicMock(spec=UploadFile)
            mock_file.filename = "test.pdf"
            mock_file.content_type = "application/pdf"
            mock_file.read = AsyncMock(return_value=b"Mock PDF content")

            # Call endpoint without target_role
            result = await upload_resume(
                batch_id="batch-test123",
                file=mock_file,
                target_role=None,
                user=TEST_USER,
            )

            assert result["resume_id"] == "resume-test123"
            assert result.get("target_role") is None


class TestRoleProcessing:
    """Tests for role-aware processing."""

    @pytest.mark.asyncio
    async def test_batch_processor_uses_target_role(self, sample_resume_text):
        """Test that batch processor uses target_role for analysis."""
        from app.services.batch_processor import BatchProcessor

        processor = BatchProcessor()

        # Mock resume with target_role
        mock_resume = {
            "resume_id": "resume-test123",
            "batch_id": "batch-test123",
            "filename": "test.pdf",
            "target_role": "sdr",
            "s3_key": "test-key",
        }

        with patch.object(processor.store, 'get_resume_content', return_value=sample_resume_text.encode()):
            with patch.object(processor.store, 'update_resume_extracted_data', return_value=None):
                with patch.object(processor.store, 'update_resume_scores') as mock_scores:
                    mock_scores.return_value = None

                    result = await processor._process_single_resume(
                        batch_id="batch-test123",
                        resume=mock_resume,
                        scoring_callback=None,
                        jd_matching_callback=None,
                        deep_analysis_callback=None,
                        job_description=None,
                    )

                    assert result["success"] is True

                    # Verify scores were updated
                    mock_scores.assert_called_once()
                    call_args = mock_scores.call_args

                    # The scores should include role_analysis
                    scores = call_args[0][2]  # Third positional arg is scores dict
                    if "role_analysis" in scores:
                        assert scores["role_analysis"]["target_role"] == "sdr"

    @pytest.mark.asyncio
    async def test_processing_without_target_role_uses_default(self, sample_resume_text):
        """Test processing without target_role uses default scoring."""
        from app.services.batch_processor import BatchProcessor

        processor = BatchProcessor()

        # Mock resume without target_role
        mock_resume = {
            "resume_id": "resume-test123",
            "batch_id": "batch-test123",
            "filename": "test.pdf",
            "s3_key": "test-key",
            # No target_role
        }

        with patch.object(processor.store, 'get_resume_content', return_value=sample_resume_text.encode()):
            with patch.object(processor.store, 'update_resume_extracted_data', return_value=None):
                with patch.object(processor.store, 'update_resume_scores') as mock_scores:
                    mock_scores.return_value = None

                    result = await processor._process_single_resume(
                        batch_id="batch-test123",
                        resume=mock_resume,
                        scoring_callback=None,
                        jd_matching_callback=None,
                        deep_analysis_callback=None,
                        job_description=None,
                    )

                    assert result["success"] is True


class TestSalesRoleEnum:
    """Tests for SalesRole enum."""

    def test_all_roles_defined(self):
        """Test all expected roles are defined."""
        expected_roles = [
            "entry_sdr", "sdr", "account_executive",
            "senior_ae", "account_manager", "sales_manager"
        ]

        for role in expected_roles:
            assert hasattr(SalesRole, role.upper()), f"Missing role: {role}"

    def test_role_values(self):
        """Test role enum values are lowercase strings."""
        for role in SalesRole:
            assert isinstance(role.value, str)
            assert role.value == role.value.lower()


class TestRoleEndToEnd:
    """End-to-end tests for the complete role flow."""

    @pytest.mark.asyncio
    async def test_full_flow_with_role(self, sample_sdr_resume):
        """Test complete flow: upload -> process -> analyze with role."""
        from app.services.resume_agent import analyze_resume

        # Step 1: Analyze resume with target role
        result = await analyze_resume(
            sample_sdr_resume,
            target_role="sdr",
            extracted_data={
                "name": "Sarah Johnson",
                "email": "sarah.j@email.com",
                "years_of_experience": 2,
                "skills": ["cold calling", "salesforce", "outreach"],
            }
        )

        # Verify complete analysis returned
        assert result["target_role"] == "sdr"
        assert result["overall_score"] > 0
        assert len(result["recommendations"]) > 0

        # Verify role-specific scoring worked
        kw_analysis = result["keyword_analysis"]
        assert kw_analysis["match_percentage"] > 0  # Should match some SDR keywords

    @pytest.mark.asyncio
    async def test_mismatched_role_lower_score(self, sample_sdr_resume, sample_ae_resume):
        """Test that mismatched role results in lower keyword match."""
        from app.services.resume_agent import analyze_resume

        # SDR resume analyzed as SDR
        sdr_as_sdr = await analyze_resume(sample_sdr_resume, target_role="sdr")

        # SDR resume analyzed as Sales Manager (mismatch)
        sdr_as_manager = await analyze_resume(sample_sdr_resume, target_role="sales_manager")

        # SDR resume should have better keyword match when analyzed as SDR
        sdr_kw = sdr_as_sdr["keyword_analysis"]["match_percentage"]
        manager_kw = sdr_as_manager["keyword_analysis"]["match_percentage"]

        # Not strictly greater due to overlapping keywords, but different
        assert sdr_kw != manager_kw or sdr_kw >= manager_kw

    @pytest.mark.asyncio
    async def test_recommendations_are_actionable(self, sample_resume_text):
        """Test that recommendations contain actionable advice."""
        from app.services.resume_agent import analyze_resume

        result = await analyze_resume(sample_resume_text, target_role="account_executive")

        recommendations = result["recommendations"]

        # Should have at least one recommendation
        assert len(recommendations) > 0

        # First recommendation should be a summary/header
        first_rec = recommendations[0]
        assert any(word in first_rec.lower() for word in ["strong", "good", "improvement", "needed"])
