"""AI-powered value evaluation using Claude."""

import json
import logging
import os
from datetime import UTC, datetime

from anthropic import Anthropic

from models.opportunity import OpportunityAssessment
from models.paper import Paper

from .blocker_detector import BlockerDetector
from .confidence_calculator import ConfidenceCalculator

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
        """Evaluate opportunity with AI and quality controls."""
        # Calculate aggregate signal scores
        signal_scores = {category: data["score"] for category, data in signals.items()}

        # Create prompt for Claude
        prompt = self._create_evaluation_prompt(paper, signals, signal_scores)

        try:
            # Call Claude
            response = self.client.messages.create(
                model="claude-3-haiku-20240307", max_tokens=2000, messages=[{"role": "user", "content": prompt}]
            )

            # Parse response - handle different content block types
            result_text = ""
            for block in response.content:
                if hasattr(block, "text"):
                    result_text = block.text  # type: ignore[attr-defined]
                    break

            data = self._parse_ai_response(result_text)

            if not data:
                return None

            # Extract or calculate dual scores
            tech_score = data.get("technical_contribution_score", 0.0)
            commercial_score = data.get("commercial_viability_score", 0.0)

            # Calculate weighted value_score (30% technical, 70% commercial)
            value_score = (tech_score * 0.3) + (commercial_score * 0.7)

            # Detect blockers
            blocker_detector = BlockerDetector()

            # Try structured blockers first
            blockers = blocker_detector.detect_from_structured(data.get("blockers", []))

            # Fallback to text-based detection if no structured blockers
            if not blockers and data.get("concerns"):
                blockers = blocker_detector.detect_from_text(data["concerns"])

            # Calculate confidence with uncertainty detection
            confidence_calc = ConfidenceCalculator()
            confidence, uncertainty_sources = confidence_calc.calculate(data)

            # Create assessment with all new fields
            assessment = OpportunityAssessment(
                id=self._generate_id(),
                paper=paper,
                data_type_name=data.get("data_type_name", "Unknown Dataset Type"),
                business_context=data.get("business_context", ""),
                value_score=value_score,
                confidence_score=confidence,
                tier="",  # Will be calculated by __post_init__ using effective_value_score
                signals_detected=signal_scores,
                detected_at=datetime.now(UTC),
                target_customers=data.get("target_customers", ""),
                market_gap=data.get("market_gap", ""),
                concerns=data.get("concerns", ""),
                data_efficiency=data.get("data_efficiency", 0.0),
                source_quality=data.get("source_quality", 0.0),
                generalizability=data.get("generalizability", 0.0),
                dataset_description=data.get("dataset_description", ""),
                data_collection_method=data.get("data_collection_method", ""),
                replication_feasibility=data.get("replication_feasibility", ""),
                # NEW FIELDS
                technical_contribution_score=tech_score,
                commercial_viability_score=commercial_score,
                blockers=blockers,
                uncertainty_sources=uncertainty_sources,
                effective_value_score=0.0,  # Will be calculated by __post_init__
            )

            # Calculate tier based on effective score (after blocker caps)
            assessment.tier = assessment.calculate_tier()

            return assessment

        except Exception as e:
            logger.error(f"Error evaluating paper {paper.id}: {e}")
            return None

    def _create_evaluation_prompt(self, paper: Paper, signals: dict, signal_scores: dict) -> str:
        """Create evaluation prompt for Claude with dual scoring."""
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
Evaluate this paper on TWO INDEPENDENT dimensions:

1. TECHNICAL CONTRIBUTION (0-10):
   - How novel/significant is the research?
   - Is methodology rigorous and reproducible?
   - Does it advance state-of-the-art?

2. COMMERCIAL VIABILITY (0-10):
   - Clear target customers with validated demand?
   - Data legally/ethically collectable?
   - Viable pricing and distribution?
   - Competitive differentiation clear?

3. BLOCKERS DETECTION:
   Identify any blockers preventing commercialization:

   Categories:
   - LEGAL: Privacy, IP, regulatory (e.g., protected attributes, GDPR)
   - TECHNICAL: Validation gaps, reproducibility (e.g., synthetic data only)
   - MARKET: Customer access, distribution (e.g., extremely niche)
   - ECONOMIC: Cost structure, pricing (e.g., cost prohibitive)

   Severity:
   - HIGH: Fundamental barrier requiring major resolution
   - MEDIUM: Significant concern requiring investigation
   - LOW: Minor issue easily addressed

Return ONLY valid JSON with this exact structure:
{{
    "technical_contribution_score": <float 0-10>,
    "commercial_viability_score": <float 0-10>,

    "blockers": [
        {{
            "category": "<legal|technical|market|economic>",
            "severity": "<high|medium|low>",
            "description": "<specific concern>"
        }}
    ],

    "data_type_name": "<concise name>",
    "business_context": "<3-4 sentences explaining commercial value with SPECIFIC EVIDENCE>",
    "market_gap": "<concrete unmet need, not 'lack of datasets'>",
    "target_customers": "<NAMED industries/roles, not generic 'researchers'>",
    "concerns": "<risks and limitations>",

    "data_efficiency": <float 0-10>,
    "source_quality": <float 0-10>,
    "generalizability": <float 0-10>,

    "dataset_description": "<describe the specific dataset(s) used in this research>",
    "data_collection_method": "<how did researchers obtain/collect this data>",
    "replication_feasibility": "<low/medium/high feasibility with 2-3 sentence reasoning>"
}}

DATA PROVENANCE ANALYSIS:
- Dataset Description: What specific data did they use? (e.g., "10,000 chest X-rays from 3 hospitals")
- Collection Method: How was it obtained? (e.g., "Manual annotation by radiologists", "Web scraping", "Sensor data")
- Replication Feasibility:
  * HIGH: Easily accessible at scale (public data, APIs, common sensors)
  * MEDIUM: Requires partnerships or moderate effort (requires IRB, vendor relationships)
  * LOW: Difficult/expensive to replicate (rare conditions, specialized equipment, privacy barriers)
  Always include reasoning (2-3 sentences)

CRITICAL GUIDELINES:
- Technical score ≠ Commercial score (research novelty ≠ market readiness)
- Generic language ("high demand across industries") → FLAG as blocker
- Missing validation → BLOCKER detection required
- Be pessimistic on commercial viability without evidence

SCORING CRITERIA:
- Technical (8-10): Major breakthrough + rigorous validation + reproducible
- Technical (6-7.9): Solid contribution + reasonable validation
- Commercial (8-10): Clear buyers + proven demand + viable economics
- Commercial (6-7.9): Some customers identified + emerging demand

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
