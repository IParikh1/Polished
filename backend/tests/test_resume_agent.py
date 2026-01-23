"""
Unit tests for the Resume Agent service.
Tests role-specific analysis and prompt generation.
"""

import pytest
from app.services.resume_agent import (
    ResumeAgent,
    get_agent,
    analyze_resume,
    get_system_prompt,
    get_role_keywords,
    ROLE_CONFIGS,
    SalesRole,
)
from app.services.prompts import BASE_TECH_SALES_PROMPT
from app.services.prompts.role_prompts import ROLE_PROMPTS


class TestResumeAgent:
    """Tests for ResumeAgent class."""

    def test_get_agent_singleton(self):
        """Test that get_agent returns a singleton."""
        agent1 = get_agent()
        agent2 = get_agent()
        assert agent1 is agent2

    def test_all_roles_have_configs(self):
        """Test that all SalesRole enum values have configurations."""
        for role in SalesRole:
            assert role.value in ROLE_CONFIGS, f"Missing config for {role.value}"

    def test_role_configs_have_required_fields(self):
        """Test that each role config has all required fields."""
        required_fields = [
            "role", "display_name", "keywords", "metrics_keywords",
            "experience_range", "scoring_weights"
        ]

        for role_id, config in ROLE_CONFIGS.items():
            for field in required_fields:
                assert hasattr(config, field), f"Missing {field} in {role_id} config"

            # Validate experience range
            min_years, max_years = config.experience_range
            assert min_years >= 0, f"Invalid min_years for {role_id}"
            assert max_years > min_years, f"Invalid max_years for {role_id}"

            # Validate keywords are present
            assert len(config.keywords) > 0, f"No keywords for {role_id}"
            assert len(config.metrics_keywords) > 0, f"No metrics keywords for {role_id}"


class TestSystemPrompt:
    """Tests for system prompt generation."""

    def test_base_prompt_included(self):
        """Test that base prompt is always included."""
        agent = get_agent()
        prompt = agent.get_system_prompt()

        # Check key elements from base prompt
        assert "Tech Sales Resume Specialist" in prompt
        assert "CRITICAL RULES" in prompt
        assert "Absolute Factual Accuracy" in prompt

    def test_role_prompt_included(self):
        """Test that role-specific prompt is included when role specified."""
        agent = get_agent()

        for role_id in ROLE_CONFIGS.keys():
            prompt = agent.get_system_prompt(role=role_id)

            # Each role prompt should have role context
            assert "Role Context" in prompt or role_id in prompt.lower()

    def test_sdr_prompt_content(self):
        """Test SDR prompt has relevant content."""
        prompt = get_system_prompt(role="sdr")

        assert "SDR" in prompt or "sdr" in prompt.lower()
        assert "quota" in prompt.lower()
        assert "meetings" in prompt.lower()

    def test_ae_prompt_content(self):
        """Test AE prompt has relevant content."""
        prompt = get_system_prompt(role="account_executive")

        assert "Account Executive" in prompt or "AE" in prompt
        assert "quota" in prompt.lower()
        assert "deal" in prompt.lower() or "acv" in prompt.lower()

    def test_senior_ae_prompt_content(self):
        """Test Senior AE prompt has enterprise content."""
        prompt = get_system_prompt(role="senior_ae")

        assert "enterprise" in prompt.lower() or "senior" in prompt.lower()
        assert "c-suite" in prompt.lower() or "executive" in prompt.lower()

    def test_jd_matching_included(self):
        """Test JD matching prompt inclusion."""
        agent = get_agent()

        prompt_without = agent.get_system_prompt(role="sdr", include_jd_matching=False)
        prompt_with = agent.get_system_prompt(role="sdr", include_jd_matching=True)

        assert len(prompt_with) > len(prompt_without)
        assert "job description" in prompt_with.lower() or "match" in prompt_with.lower()


class TestRoleKeywords:
    """Tests for role-specific keywords."""

    def test_sdr_keywords(self):
        """Test SDR role has relevant keywords."""
        keywords = get_role_keywords("sdr")

        assert "cold calling" in keywords or "outbound" in keywords
        assert "quota" in keywords or "meetings booked" in keywords
        assert "salesforce" in keywords or "outreach" in keywords

    def test_ae_keywords(self):
        """Test AE role has relevant keywords."""
        keywords = get_role_keywords("account_executive")

        assert any(kw in keywords for kw in ["quota", "acv", "closed won", "pipeline"])
        assert any(kw in keywords for kw in ["meddic", "bant", "challenger"])

    def test_am_keywords(self):
        """Test Account Manager role has retention keywords."""
        keywords = get_role_keywords("account_manager")

        assert any(kw in keywords for kw in ["nrr", "retention", "churn", "renewal"])
        assert any(kw in keywords for kw in ["upsell", "expansion", "cross-sell"])

    def test_invalid_role_returns_empty(self):
        """Test invalid role returns empty keyword list."""
        keywords = get_role_keywords("invalid_role")
        assert keywords == []


class TestResumeAnalysis:
    """Tests for resume analysis functionality."""

    @pytest.mark.asyncio
    async def test_analyze_resume_returns_dict(self, sample_resume_text):
        """Test that analyze_resume returns expected structure."""
        result = await analyze_resume(
            sample_resume_text,
            target_role="sdr"
        )

        assert isinstance(result, dict)
        assert "target_role" in result
        assert "scores" in result
        assert "overall_score" in result
        assert "keyword_analysis" in result
        assert "recommendations" in result

    @pytest.mark.asyncio
    async def test_sdr_analysis_scores(self, sample_sdr_resume):
        """Test SDR resume gets appropriate scores."""
        result = await analyze_resume(
            sample_sdr_resume,
            target_role="sdr"
        )

        scores = result["scores"]

        # SDR resume should score well on SDR-specific criteria
        assert scores["overall"] > 0
        assert "keyword_match" in scores
        assert "metrics_presence" in scores

    @pytest.mark.asyncio
    async def test_ae_analysis_scores(self, sample_ae_resume):
        """Test AE resume gets appropriate scores."""
        result = await analyze_resume(
            sample_ae_resume,
            target_role="account_executive"
        )

        scores = result["scores"]

        # AE resume should score well on AE criteria
        assert scores["overall"] >= 45  # Should be a reasonable score
        assert "quantification" in scores

    @pytest.mark.asyncio
    async def test_keyword_analysis_structure(self, sample_resume_text):
        """Test keyword analysis returns expected structure."""
        result = await analyze_resume(
            sample_resume_text,
            target_role="sdr"
        )

        kw_analysis = result["keyword_analysis"]

        assert "matched" in kw_analysis
        assert "missing" in kw_analysis
        assert "match_percentage" in kw_analysis
        assert isinstance(kw_analysis["matched"], list)
        assert isinstance(kw_analysis["missing"], list)

    @pytest.mark.asyncio
    async def test_recommendations_generated(self, sample_resume_text):
        """Test that recommendations are generated."""
        result = await analyze_resume(
            sample_resume_text,
            target_role="sdr"
        )

        recommendations = result["recommendations"]

        assert isinstance(recommendations, list)
        assert len(recommendations) > 0

    @pytest.mark.asyncio
    async def test_no_role_still_works(self, sample_resume_text):
        """Test analysis works without specifying a role."""
        result = await analyze_resume(
            sample_resume_text,
            target_role=None
        )

        assert "scores" in result
        assert "overall_score" in result
        assert result["target_role"] is None

    @pytest.mark.asyncio
    async def test_experience_fit_scoring(self, sample_ae_resume):
        """Test experience fit is calculated correctly."""
        # AE resume with 5+ years for senior_ae role
        result = await analyze_resume(
            sample_ae_resume,
            target_role="senior_ae",
            extracted_data={"years_of_experience": 6}
        )

        scores = result["scores"]
        assert "experience_fit" in scores
        # 6 years should fit well for senior_ae (5-15 range)
        assert scores["experience_fit"] >= 80

    @pytest.mark.asyncio
    async def test_metrics_analysis(self, sample_resume_text):
        """Test metrics analysis identifies quantified achievements."""
        result = await analyze_resume(
            sample_resume_text,
            target_role="sdr"
        )

        metrics = result["metrics_analysis"]

        assert "found_metrics" in metrics
        assert "metrics_score" in metrics

        # Sample resume has percentages and numbers
        found = metrics["found_metrics"]
        assert len(found) > 0


class TestRoleComparison:
    """Tests for comparing analysis across different roles."""

    @pytest.mark.asyncio
    async def test_same_resume_different_roles(self, sample_sdr_resume):
        """Test same resume scored differently for different roles."""
        sdr_result = await analyze_resume(sample_sdr_resume, target_role="sdr")
        ae_result = await analyze_resume(sample_sdr_resume, target_role="account_executive")

        # SDR resume should score better as SDR than as AE
        # (since it lacks AE-specific metrics like deal size, win rate)
        sdr_kw_match = sdr_result["keyword_analysis"]["match_percentage"]
        ae_kw_match = ae_result["keyword_analysis"]["match_percentage"]

        # Should have different keyword matches
        assert sdr_kw_match != ae_kw_match

    @pytest.mark.asyncio
    async def test_role_display_name_included(self, sample_resume_text):
        """Test role display name is included in results."""
        result = await analyze_resume(sample_resume_text, target_role="account_executive")

        assert "role_display_name" in result
        assert "Account Executive" in result["role_display_name"]
