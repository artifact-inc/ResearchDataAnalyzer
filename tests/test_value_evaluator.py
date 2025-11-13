"""Tests for AI-powered value evaluation."""

import json
import time
from unittest.mock import Mock, patch

import pytest

from analyzers.value_evaluator import ValueEvaluator
from models.paper import Paper


class TestValueEvaluator:
    """Tests for ValueEvaluator."""

    @pytest.fixture
    def config(self) -> dict:
        """Evaluation configuration."""
        return {
            "tier_thresholds": {"high": 8.0, "medium": 6.0},
        }

    @pytest.fixture
    def evaluator(self, config: dict) -> ValueEvaluator:
        """Create ValueEvaluator instance."""
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test_key"}):
            return ValueEvaluator(config)

    @pytest.mark.asyncio
    async def test_evaluate_success(
        self, evaluator: ValueEvaluator, sample_paper: Paper, sample_signals: dict[str, dict], config: dict
    ) -> None:
        """Test successful evaluation."""
        mock_response_data = {
            "value_score": 8.5,
            "confidence": 8.0,
            "data_type_name": "Medical Imaging Dataset",
            "business_context": "High-quality medical imaging for few-shot learning",
            "market_gap": "Lack of expert-annotated medical datasets",
            "target_customers": "Healthcare AI companies",
            "concerns": "Regulatory compliance required",
            "data_efficiency": 8.5,
            "source_quality": 9.0,
            "generalizability": 7.5,
        }

        with patch("anthropic.Anthropic") as mock_anthropic:
            mock_client = Mock()
            mock_message = Mock()
            mock_content = Mock()
            mock_content.text = json.dumps(mock_response_data)
            mock_message.content = [mock_content]
            mock_client.messages.create.return_value = mock_message
            mock_anthropic.return_value = mock_client

            # Recreate evaluator with mocked client
            with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test_key"}):
                evaluator = ValueEvaluator(config)
                evaluator.client = mock_client

                assessment = await evaluator.evaluate(sample_paper, sample_signals, config)

            assert assessment is not None
            assert assessment.value_score == 8.5
            assert assessment.confidence_score == 8.0
            assert assessment.tier == "A"  # Tier is calculated based on thresholds
            assert assessment.data_efficiency == 8.5
            assert assessment.source_quality == 9.0
            assert assessment.generalizability == 7.5
            assert assessment.data_type_name == "Medical Imaging Dataset"

    @pytest.mark.asyncio
    async def test_evaluate_api_error(
        self, evaluator: ValueEvaluator, sample_paper: Paper, sample_signals: dict[str, dict], config: dict
    ) -> None:
        """Test evaluation handling API errors."""
        with patch("anthropic.Anthropic") as mock_anthropic:
            mock_client = Mock()
            mock_client.messages.create.side_effect = Exception("API Error")
            mock_anthropic.return_value = mock_client

            with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test_key"}):
                evaluator = ValueEvaluator(config)
                evaluator.client = mock_client

                assessment = await evaluator.evaluate(sample_paper, sample_signals, config)

            assert assessment is None

    @pytest.mark.asyncio
    async def test_evaluate_invalid_json(
        self, evaluator: ValueEvaluator, sample_paper: Paper, sample_signals: dict[str, dict], config: dict
    ) -> None:
        """Test evaluation with invalid JSON response."""
        with patch("anthropic.Anthropic") as mock_anthropic:
            mock_client = Mock()
            mock_message = Mock()
            mock_content = Mock()
            mock_content.text = "This is not valid JSON"
            mock_message.content = [mock_content]
            mock_client.messages.create.return_value = mock_message
            mock_anthropic.return_value = mock_client

            with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test_key"}):
                evaluator = ValueEvaluator(config)
                evaluator.client = mock_client

                assessment = await evaluator.evaluate(sample_paper, sample_signals, config)

            assert assessment is None

    def test_parse_ai_response_valid_json(self, evaluator: ValueEvaluator) -> None:
        """Test parsing valid JSON response."""
        response_text = json.dumps({"value_score": 8.0, "confidence": 7.5})

        result = evaluator._parse_ai_response(response_text)

        assert result is not None
        assert result["value_score"] == 8.0
        assert result["confidence"] == 7.5

    def test_parse_ai_response_with_markdown(self, evaluator: ValueEvaluator) -> None:
        """Test parsing JSON wrapped in markdown."""
        response_text = '```json\n{"value_score": 8.0}\n```'

        result = evaluator._parse_ai_response(response_text)

        assert result is not None
        assert result["value_score"] == 8.0

    def test_parse_ai_response_invalid(self, evaluator: ValueEvaluator) -> None:
        """Test parsing invalid JSON."""
        response_text = "Not JSON at all"

        result = evaluator._parse_ai_response(response_text)

        assert result is None

    def test_create_evaluation_prompt(
        self, evaluator: ValueEvaluator, sample_paper: Paper, sample_signals: dict[str, dict]
    ) -> None:
        """Test evaluation prompt creation."""
        signal_scores = {category: data["score"] for category, data in sample_signals.items()}

        prompt = evaluator._create_evaluation_prompt(sample_paper, sample_signals, signal_scores)

        # Check key sections are present
        assert "PAPER INFORMATION" in prompt
        assert sample_paper.title in prompt
        assert "DETECTED SIGNALS" in prompt
        assert "ENHANCED QUALITY & SCALING SIGNALS" in prompt
        assert "data_efficiency" in prompt
        assert "source_quality" in prompt
        assert "generalizability" in prompt

    def test_generate_id(self, evaluator: ValueEvaluator) -> None:
        """Test ID generation format."""
        id1 = evaluator._generate_id()
        time.sleep(0.01)  # Ensure different timestamp
        id2 = evaluator._generate_id()

        assert id1.startswith("rdla_")
        assert id2.startswith("rdla_")
        # IDs should be unique (unless generated at exact same microsecond)
        # Just verify format is correct
        assert len(id1) > 5

    def test_missing_api_key(self) -> None:
        """Test that missing API key raises error."""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
                ValueEvaluator({})
