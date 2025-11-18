"""Confidence calculation for opportunity assessments."""

import re

from models.opportunity import UncertaintySource


class ConfidenceCalculator:
    """Calculates confidence scores based on uncertainty sources."""

    # Uncertainty penalty mapping (points to deduct from 10.0)
    UNCERTAINTY_PENALTIES: dict[str, float] = {
        "missing_market_validation": 2.0,
        "vague_business_opportunity": 1.5,
        "severe_concerns_understated": 2.5,
        "no_enhanced_dimensions": 1.0,
        "synthetic_data_only": 1.5,
        "no_customer_validation": 2.0,
        "unclear_pricing": 1.0,
        "limited_evidence": 1.5,
        "unclear_target_customers": 1.5,
        "hypothetical_use_cases": 2.0,
    }

    # Detection patterns for uncertainty indicators
    UNCERTAINTY_INDICATORS: dict[str, list[str]] = {
        "missing_market_validation": [
            r"no market validation",
            r"market unclear",
            r"demand unproven",
            r"market.*not.*validated",
        ],
        "vague_business_opportunity": [
            r"high demand across industries",
            r"various use cases",
            r"potential applications",
            r"could be useful",
            r"might be valuable",
            r"possibly beneficial",
        ],
        "severe_concerns_understated": [
            r"(?i)however.*significant",
            r"(?i)but.*critical",
            r"(?i)although.*major",
            r"(?i)despite.*serious",
        ],
        "synthetic_data_only": [
            r"synthetic data",
            r"simulated results",
            r"benchmark only",
            r"artificial.*data",
        ],
        "no_customer_validation": [
            r"no customer feedback",
            r"not tested with users",
            r"hypothetical customers",
            r"assumed.*customers?",
        ],
        "unclear_pricing": [
            r"pricing uncertain",
            r"monetization unclear",
            r"revenue model undefined",
            r"pricing.*not.*clear",
        ],
        "limited_evidence": [
            r"limited evidence",
            r"unclear evidence",
            r"evidence.*lacking",
            r"insufficient.*data",
        ],
        "unclear_target_customers": [
            r"target.*unclear",
            r"customers?.*unspecified",
            r"audience.*undefined",
        ],
        "hypothetical_use_cases": [
            r"potential.*use",
            r"could.*apply",
            r"might.*serve",
            r"theoretical.*application",
        ],
    }

    def calculate(self: "ConfidenceCalculator", evaluation_data: dict) -> tuple[float, list[UncertaintySource]]:
        """Calculate confidence and identify uncertainty sources.

        Args:
            evaluation_data: Dictionary with evaluation fields

        Returns:
            Tuple of (confidence score 0-10, list of uncertainty sources)
        """
        uncertainty_sources: list[UncertaintySource] = []
        total_penalty = 0.0

        # Check for missing enhanced dimensions
        if not evaluation_data.get("enhanced_dimensions"):
            penalty = self.UNCERTAINTY_PENALTIES["no_enhanced_dimensions"]
            uncertainty_sources.append(
                UncertaintySource(description="No enhanced performance dimensions analyzed", penalty=penalty)
            )
            total_penalty += penalty

        # Combine all text fields for scanning
        text_to_scan = " ".join(
            [
                evaluation_data.get("business_opportunity", ""),
                evaluation_data.get("concerns", ""),
                evaluation_data.get("market_gap", ""),
                evaluation_data.get("target_customers", ""),
            ]
        )

        # Scan for uncertainty indicators
        for source_type, patterns in self.UNCERTAINTY_INDICATORS.items():
            if self._matches_any_pattern(text_to_scan, patterns):
                penalty = self.UNCERTAINTY_PENALTIES[source_type]

                # Extract matching sentence for description
                matching_sentence = self._extract_matching_text(text_to_scan, patterns)

                uncertainty_sources.append(UncertaintySource(description=matching_sentence, penalty=penalty))
                total_penalty += penalty

        # Calculate confidence: 10.0 - total_penalty, clamped to [0, 10]
        confidence = max(0.0, min(10.0, 10.0 - total_penalty))

        return confidence, uncertainty_sources

    def _matches_any_pattern(self: "ConfidenceCalculator", text: str, patterns: list[str]) -> bool:
        """Check if text matches any of the given patterns.

        Args:
            text: Text to search
            patterns: List of regex patterns

        Returns:
            True if any pattern matches
        """
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

    def _extract_matching_text(self: "ConfidenceCalculator", text: str, patterns: list[str]) -> str:
        """Extract sentence or phrase containing pattern match.

        Args:
            text: Full text to search
            patterns: List of regex patterns

        Returns:
            Sentence containing the match, or generic description
        """
        sentences = text.split(".")

        for pattern in patterns:
            for sentence in sentences:
                if re.search(pattern, sentence, re.IGNORECASE):
                    return sentence.strip()

        # Fallback to first pattern as description
        return patterns[0].replace(r"\s?", " ").replace("?", "").replace(r"(?i)", "")
