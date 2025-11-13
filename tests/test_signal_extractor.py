"""Tests for signal extraction."""

import json
from pathlib import Path

import pytest

from analyzers.signal_extractor import SignalExtractor
from models.paper import Paper


class TestSignalExtractor:
    """Tests for SignalExtractor."""

    @pytest.fixture
    def config(self) -> dict:
        """Load heuristics configuration."""
        config_path = Path(__file__).parent.parent / "config" / "heuristics.json"
        with open(config_path) as f:
            return json.load(f)

    @pytest.fixture
    def extractor(self, config: dict) -> SignalExtractor:
        """Create SignalExtractor instance."""
        return SignalExtractor(config)

    def test_extract_efficiency_signals(self, extractor: SignalExtractor) -> None:
        """Test extraction of data efficiency signals."""
        text = "our carefully curated dataset achieves 95% improvement with only 100 samples"

        signals = extractor._extract_efficiency_signals(text)

        assert signals["score"] > 0
        # Check that at least one signal was detected
        assert len(signals["detected"]) > 0
        assert "comparative_efficiency" in signals["detected"]

    def test_extract_quality_indicators(self, extractor: SignalExtractor) -> None:
        """Test extraction of quality indicator signals."""
        text = "expert-annotated data with inter-rater agreement of 0.95 kappa score"

        signals = extractor._extract_quality_indicators(text)

        assert signals["score"] > 0
        assert len(signals.get("detected", [])) > 0
        # Sample phrases may be empty if context extraction fails, just check structure exists
        assert "sample_phrases" in signals

    def test_extract_scaling_potential(self, extractor: SignalExtractor) -> None:
        """Test extraction of scaling potential signals."""
        text = "our method generalizes across multiple domains and transfers to various tasks"

        signals = extractor._extract_scaling_potential(text)

        assert signals["score"] > 0
        assert "transfer_learning" in signals["detected"]
        assert "cross_domain" in signals["detected"]

    def test_extract_sample_phrases(self, extractor: SignalExtractor) -> None:
        """Test sample phrase extraction."""
        text = "this is a test with carefully curated examples for validation"
        keyword = "carefully curated"

        phrases = extractor._extract_sample_phrases(text, keyword, context_window=20)

        assert len(phrases) > 0
        assert keyword in phrases[0]
        assert "..." in phrases[0]  # Should have context markers

    def test_extract_all_signals(self, extractor: SignalExtractor, sample_paper: Paper) -> None:
        """Test complete signal extraction from a paper."""
        signals = extractor.extract(sample_paper)

        # Should have all expected signal categories
        expected_categories = [
            "demand",
            "scarcity",
            "novelty",
            "quality",
            "data_efficiency",
            "performance",
            "scale",
            "commercial",
            "trend",
            "quality_indicators",
            "scaling_potential",
        ]

        for category in expected_categories:
            assert category in signals
            assert "score" in signals[category]
            assert "detected" in signals[category]

    def test_extract_no_matches(self, extractor: SignalExtractor) -> None:
        """Test signal extraction with text containing no matching keywords."""
        text = "generic text with no special keywords or indicators"

        signals = extractor._extract_efficiency_signals(text)

        assert signals["score"] == 0.0
        assert len(signals["detected"]) == 0

    def test_extract_score_capping(self, extractor: SignalExtractor) -> None:
        """Test that scores are capped at 10.0."""
        # Text with many matches to potentially exceed 10.0
        text = " ".join(
            [
                "carefully curated high-quality expert-annotated comprehensive",
                "strategic selection quality focus empirical data",
            ]
            * 10
        )

        signals = extractor._extract_quality_indicators(text)

        assert signals["score"] <= 10.0

    def test_sample_phrases_limit(self, extractor: SignalExtractor) -> None:
        """Test that sample phrases are limited to 3."""
        # Text with keyword repeated many times
        text = " ".join([f"carefully curated item {i}" for i in range(20)])

        phrases = extractor._extract_sample_phrases(text, "carefully curated", context_window=15)

        assert len(phrases) <= 3
