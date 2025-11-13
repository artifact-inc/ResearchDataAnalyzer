"""AI-powered value evaluation using Claude."""

import json
import logging
import os
from datetime import UTC, datetime

from anthropic import Anthropic

from models.opportunity import OpportunityAssessment
from models.paper import Paper

from .opportunity_scorer import calculate_tier

logger = logging.getLogger(__name__)


class ValueEvaluator:
    """Evaluate commercial value using AI."""

    def __init__(self, config: dict) -> None:
        """Initialize evaluator."""
        self.config = config
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")
        self.client = Anthropic(api_key=api_key)

    async def evaluate(self, paper: Paper, signals: dict[str, dict], config: dict) -> OpportunityAssessment | None:
        """Evaluate opportunity with AI."""
        # Calculate aggregate signal scores
        signal_scores = {category: data["score"] for category, data in signals.items()}

        # Create prompt for Claude
        prompt = self._create_evaluation_prompt(paper, signals, signal_scores)

        try:
            # Call Claude
            response = self.client.messages.create(
                model="claude-3-haiku-20240307", max_tokens=2000, messages=[{"role": "user", "content": prompt}]
            )

            # Parse response
            result_text = response.content[0].text
            data = self._parse_ai_response(result_text)

            if not data:
                return None

            # Calculate tier
            tier = calculate_tier(data["value_score"], config)

            # Create assessment
            assessment = OpportunityAssessment(
                id=self._generate_id(),
                paper=paper,
                data_type_name=data.get("data_type_name", "Unknown Dataset Type"),
                business_context=data.get("business_context", ""),
                value_score=data["value_score"],
                confidence_score=data["confidence"],
                tier=tier,
                signals_detected=signal_scores,
                detected_at=datetime.now(UTC),
                target_customers=data.get("target_customers", ""),
                market_gap=data.get("market_gap", ""),
                concerns=data.get("concerns", ""),
                data_efficiency=data.get("data_efficiency", 0.0),
                source_quality=data.get("source_quality", 0.0),
                generalizability=data.get("generalizability", 0.0),
            )

            return assessment

        except Exception as e:
            logger.error(f"Error evaluating paper {paper.id}: {e}")
            return None

    def _create_evaluation_prompt(self, paper: Paper, signals: dict, signal_scores: dict) -> str:
        """Create evaluation prompt for Claude."""
        # Build main signals summary
        signals_summary = "\n".join(
            [
                f"- {category.replace('_', ' ').title()}: {data['score']:.1f}/10 "
                f"(detected: {', '.join(data['detected']) if data['detected'] else 'none'})"
                for category, data in signals.items()
                if data["score"] > 0 and category not in ["quality_indicators", "scaling_potential"]
            ]
        )

        # Build enhanced signals with sample phrases
        enhanced_signals = []
        for category in ["quality_indicators", "scaling_potential"]:
            if category in signals and signals[category]["score"] > 0:
                data = signals[category]
                enhanced_signals.append(
                    f"- {category.replace('_', ' ').title()}: {data['score']:.1f}/10 "
                    f"(detected: {', '.join(data['detected']) if data['detected'] else 'none'})"
                )
                if data.get("sample_phrases"):
                    for phrase in data["sample_phrases"]:
                        enhanced_signals.append(f'  • "{phrase}"')

        enhanced_summary = "\n".join(enhanced_signals) if enhanced_signals else "None detected"

        return f"""You are analyzing research papers to identify market opportunities for creating NEW datasets.

PAPER INFORMATION:
Title: {paper.title}
Abstract: {paper.abstract[:1000]}...
Published: {paper.published_date.strftime("%Y-%m-%d")}
Citations: {paper.citation_count or "Unknown"}
Source: {paper.source}

DETECTED SIGNALS:
{signals_summary}

ENHANCED QUALITY & SCALING SIGNALS:
{enhanced_summary}

TASK:
Evaluate this paper for dataset creation opportunities. Focus on whether creating a NEW dataset
of this type would be commercially valuable.

Return ONLY valid JSON with this exact structure:
{{
    "value_score": <float 0-10>,
    "confidence": <float 0-10>,
    "data_type_name": "<concise name>",
    "business_context": "<3-4 sentences explaining commercial value>",
    "market_gap": "<what specific need exists>",
    "target_customers": "<who would buy this data>",
    "concerns": "<any red flags or risks>",
    "data_efficiency": <float 0-10>,
    "source_quality": <float 0-10>,
    "generalizability": <float 0-10>
}}

CRITERIA:
- HIGH VALUE (8-10): Clear demand + proven use cases + multiple buyers + sustainable market
- MEDIUM VALUE (6-7.9): Some demand + emerging area + moderate competition
- LOW VALUE (<6): Niche, unclear demand, or already saturated

ADDITIONAL DIMENSIONS:
- data_efficiency (0-10): How efficiently can this dataset type be collected/created relative to value?
  High = small dataset yields big gains, Low = requires massive scale
- source_quality (0-10): What's the inherent quality/reliability of data sources?
  High = expert-validated/gold-standard, Low = noisy/unreliable sources
- generalizability (0-10): How well does this dataset type transfer across domains/tasks?
  High = broad applicability, Low = narrow/specific use case

Be realistic about commercial viability. Not all interesting research translates to business opportunity.

Return only the JSON, no other text."""

    def _parse_ai_response(self, text: str) -> dict | None:
        """Parse AI response, handling various formats."""
        try:
            # Try to find JSON in the response
            json_start = text.find("{")
            json_end = text.rfind("}") + 1

            if json_start >= 0 and json_end > json_start:
                json_text = text[json_start:json_end]
                return json.loads(json_text)

            # If no JSON found, try parsing entire text
            return json.loads(text)

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            logger.debug(f"Response text: {text}")
            return None

    def _generate_id(self) -> str:
        """Generate unique finding ID."""
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        return f"rdla_{timestamp}"
