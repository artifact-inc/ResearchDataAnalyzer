"""Blocker detection for opportunity assessments."""

import re

from models.opportunity import Blocker, BlockerCategory, BlockerSeverity


class BlockerDetector:
    """Extracts commercialization blockers from evaluation text."""

    # Keyword patterns for each blocker category and severity
    BLOCKER_PATTERNS: dict[BlockerCategory, dict[BlockerSeverity, list[str]]] = {
        BlockerCategory.LEGAL: {
            BlockerSeverity.HIGH: [
                r"protected attributes?",
                r"privacy violations?",
                r"GDPR",
                r"regulatory approval required",
                r"legal restrictions?",
                r"violates.*law",
                r"illegal",
            ],
            BlockerSeverity.MEDIUM: [
                r"licensing concerns?",
                r"IP unclear",
                r"intellectual property",
                r"potential legal issues?",
                r"patent.*unclear",
            ],
            BlockerSeverity.LOW: [
                r"terms of use",
                r"attribution required",
                r"open source license",
            ],
        },
        BlockerCategory.TECHNICAL: {
            BlockerSeverity.HIGH: [
                r"cannot reproduce",
                r"no validation data",
                r"synthetic data only",
                r"theoretical only",
                r"not reproducible",
                r"no real.*data",
            ],
            BlockerSeverity.MEDIUM: [
                r"limited validation",
                r"needs further testing",
                r"benchmark only",
                r"unclear methodology",
                r"validation.*needed",
            ],
            BlockerSeverity.LOW: [
                r"minor.*issues?",
                r"some limitations?",
                r"could be improved",
            ],
        },
        BlockerCategory.MARKET: {
            BlockerSeverity.HIGH: [
                r"no clear customers?",
                r"extremely niche",
                r"no distribution channel",
                r"market.*unclear",
                r"no.*buyers?",
            ],
            BlockerSeverity.MEDIUM: [
                r"limited market",
                r"narrow use case",
                r"customer access unclear",
                r"small.*market",
            ],
            BlockerSeverity.LOW: [
                r"niche application",
                r"specialized.*use",
            ],
        },
        BlockerCategory.ECONOMIC: {
            BlockerSeverity.HIGH: [
                r"cost prohibitive",
                r"no viable pricing",
                r"negative unit economics",
                r"too expensive",
                r"economically.*infeasible",
            ],
            BlockerSeverity.MEDIUM: [
                r"expensive to produce",
                r"pricing uncertain",
                r"margin concerns?",
                r"cost.*high",
            ],
            BlockerSeverity.LOW: [
                r"minor.*cost",
                r"some.*expense",
            ],
        },
    }

    def detect_from_text(self: "BlockerDetector", concerns: str) -> list[Blocker]:
        """Extract blockers from concern text using pattern matching.

        Args:
            concerns: Evaluation concerns text

        Returns:
            List of detected blockers
        """
        blockers: list[Blocker] = []
        concerns_lower = concerns.lower()

        for category, severity_patterns in self.BLOCKER_PATTERNS.items():
            for severity, patterns in severity_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, concerns_lower):
                        # Extract sentence containing the match
                        matching_sentence = self._extract_matching_sentence(concerns, pattern)

                        blockers.append(Blocker(category=category, severity=severity, description=matching_sentence))
                        break  # One blocker per severity level per category

        return blockers

    def detect_from_structured(self: "BlockerDetector", blocker_data: list[dict]) -> list[Blocker]:
        """Extract blockers from structured Claude output.

        Args:
            blocker_data: List of blocker dictionaries with category, severity, description

        Returns:
            List of Blocker objects
        """
        blockers: list[Blocker] = []

        for item in blocker_data:
            try:
                blockers.append(
                    Blocker(
                        category=BlockerCategory(item["category"]),
                        severity=BlockerSeverity(item["severity"]),
                        description=item["description"],
                    )
                )
            except (KeyError, ValueError):
                # Skip malformed blocker data
                continue

        return blockers

    def _extract_matching_sentence(self: "BlockerDetector", text: str, pattern: str) -> str:
        """Extract the sentence containing the pattern match.

        Args:
            text: Full text to search
            pattern: Regex pattern that matched

        Returns:
            Sentence containing the match, or the pattern itself as fallback
        """
        sentences = text.split(".")
        for sentence in sentences:
            if re.search(pattern, sentence.lower()):
                return sentence.strip()

        # Fallback to pattern if sentence extraction fails
        return pattern.replace(r"\s?", " ").replace("?", "")
