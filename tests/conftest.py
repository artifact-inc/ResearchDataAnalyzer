"""Pytest configuration and shared fixtures."""

from datetime import UTC, datetime
from pathlib import Path

import pytest

from models.opportunity import OpportunityAssessment
from models.paper import Paper


@pytest.fixture
def sample_paper() -> Paper:
    """Sample paper for testing."""
    return Paper(
        id="arxiv_2501.12345",
        title="High-Quality Medical Imaging Dataset for Few-Shot Learning",
        abstract="We present a carefully curated dataset of 500 expert-annotated medical images...",
        authors=["Jane Smith", "John Doe"],
        published_date=datetime(2025, 1, 10, tzinfo=UTC),
        source="arxiv",
        url="http://arxiv.org/abs/2501.12345v1",
        citation_count=15,
        venue="NeurIPS",
    )


@pytest.fixture
def sample_signals() -> dict[str, dict]:
    """Sample signal extraction results."""
    return {
        "demand": {"score": 7.5, "detected": ["scarcity_complaint"]},
        "scarcity": {"score": 8.0, "detected": ["privacy_restriction"]},
        "novelty": {"score": 6.0, "detected": ["novelty_markers"]},
        "quality": {"score": 9.0, "detected": ["expert_involvement", "quality_emphasis"]},
        "data_efficiency": {"score": 8.5, "detected": ["efficiency_emphasis", "comparative_efficiency"]},
        "performance": {"score": 7.0, "detected": ["quantified_impact"]},
        "scale": {"score": 5.0, "detected": ["scale_opportunity"]},
        "commercial": {"score": 6.5, "detected": ["industry_mention"]},
        "trend": {"score": 5.0, "detected": ["moderate_citation"]},
        "quality_indicators": {
            "score": 8.0,
            "detected": ["quality_kw_expert", "quantified_agreement"],
            "sample_phrases": ["...carefully curated dataset...", "...expert-annotated medical images..."],
        },
        "scaling_potential": {
            "score": 7.0,
            "detected": ["transfer_learning", "cross_domain"],
            "sample_phrases": ["...generalizes across multiple tasks..."],
        },
    }


@pytest.fixture
def sample_assessment(sample_paper: Paper) -> OpportunityAssessment:
    """Sample opportunity assessment."""
    return OpportunityAssessment(
        id="rdla_20250115_120000",
        paper=sample_paper,
        data_type_name="Medical Imaging Dataset",
        business_context="High-quality medical imaging datasets enable few-shot learning applications.",
        value_score=8.5,
        confidence_score=8.0,
        tier="High Value",
        signals_detected={"demand": 7.5, "quality": 9.0, "data_efficiency": 8.5},
        detected_at=datetime(2025, 1, 15, 12, 0, 0, tzinfo=UTC),
        target_customers="Healthcare AI companies, medical research institutions",
        market_gap="Lack of expert-annotated datasets for few-shot medical imaging",
        concerns="Regulatory compliance, data privacy considerations",
        data_efficiency=8.5,
        source_quality=9.0,
        generalizability=7.5,
    )


@pytest.fixture
def fixtures_dir() -> Path:
    """Path to test fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def arxiv_sample_xml(fixtures_dir: Path) -> str:
    """Load sample arXiv XML response."""
    return (fixtures_dir / "arxiv_sample.xml").read_text()


@pytest.fixture
def s2_sample_json(fixtures_dir: Path) -> str:
    """Load sample Semantic Scholar JSON response."""
    return (fixtures_dir / "s2_sample.json").read_text()
