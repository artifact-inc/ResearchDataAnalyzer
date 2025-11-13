"""Tests for data models."""

from datetime import UTC, datetime

import pytest

from models.opportunity import OpportunityAssessment
from models.paper import Paper


class TestPaper:
    """Tests for Paper model."""

    def test_valid_paper_creation(self, sample_paper: Paper) -> None:
        """Test creating a valid Paper."""
        assert sample_paper.id == "arxiv_2501.12345"
        assert sample_paper.title == "High-Quality Medical Imaging Dataset for Few-Shot Learning"
        assert len(sample_paper.authors) == 2
        assert sample_paper.citation_count == 15

    def test_paper_minimal_fields(self) -> None:
        """Test Paper with only required fields."""
        paper = Paper(
            id="test_123",
            title="Test Paper",
            abstract="Test abstract",
            authors=["Test Author"],
            published_date=datetime.now(UTC),
            source="arxiv",
            url="https://example.com/paper",
        )
        assert paper.citation_count is None
        assert paper.venue is None

    def test_paper_missing_required_fields(self) -> None:
        """Test that Paper validation fails with missing required fields."""
        with pytest.raises(TypeError):  # Pydantic v2 raises TypeError for missing positional args
            Paper(
                id="test_123",
                title="Test Paper",
                # Missing other required fields
            )

    def test_paper_date_handling(self) -> None:
        """Test that Paper handles datetime properly."""
        now = datetime.now(UTC)
        paper = Paper(
            id="test_123",
            title="Test",
            abstract="Test",
            authors=["Author"],
            published_date=now,
            source="arxiv",
            url="https://example.com",
        )
        assert paper.published_date == now
        assert paper.published_date.tzinfo is not None


class TestOpportunityAssessment:
    """Tests for OpportunityAssessment model."""

    def test_valid_assessment_creation(self, sample_assessment: OpportunityAssessment) -> None:
        """Test creating a valid OpportunityAssessment."""
        assert sample_assessment.value_score == 8.5
        assert sample_assessment.confidence_score == 8.0
        assert sample_assessment.tier == "High Value"
        assert sample_assessment.data_efficiency == 8.5
        assert sample_assessment.source_quality == 9.0
        assert sample_assessment.generalizability == 7.5

    def test_assessment_with_minimal_fields(self, sample_paper: Paper) -> None:
        """Test OpportunityAssessment with minimal fields."""
        assessment = OpportunityAssessment(
            id="test_123",
            paper=sample_paper,
            data_type_name="Test Dataset",
            business_context="Test context",
            value_score=5.0,
            confidence_score=6.0,
            tier="Medium Value",
            signals_detected={},
            detected_at=datetime.now(UTC),
        )
        # Check default values
        assert assessment.data_efficiency == 0.0
        assert assessment.source_quality == 0.0
        assert assessment.generalizability == 0.0

    def test_score_validation_ranges(self, sample_paper: Paper) -> None:
        """Test that scores are validated within 0-10 range."""
        # Valid scores (0-10)
        assessment = OpportunityAssessment(
            id="test_123",
            paper=sample_paper,
            data_type_name="Test",
            business_context="Test",
            value_score=10.0,
            confidence_score=0.0,
            tier="Test",
            signals_detected={},
            detected_at=datetime.now(UTC),
            data_efficiency=5.0,
            source_quality=7.5,
            generalizability=10.0,
        )
        assert assessment.data_efficiency == 5.0
        assert assessment.source_quality == 7.5
        assert assessment.generalizability == 10.0

    def test_signals_detected_dict(self, sample_assessment: OpportunityAssessment) -> None:
        """Test that signals_detected properly stores signal scores."""
        assert "demand" in sample_assessment.signals_detected
        assert "quality" in sample_assessment.signals_detected
        assert sample_assessment.signals_detected["demand"] == 7.5
        assert sample_assessment.signals_detected["quality"] == 9.0
