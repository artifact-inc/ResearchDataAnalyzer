"""Signal extraction using keyword heuristics."""

import logging
import re

from models.paper import Paper

logger = logging.getLogger(__name__)


class SignalExtractor:
    """Extract value signals from papers using keyword heuristics."""

    def __init__(self, config: dict) -> None:
        """Initialize with heuristics configuration."""
        self.config = config
        self.keywords = config.get("keywords", {})

    def extract(self, paper: Paper) -> dict[str, dict]:
        """Extract all signals from a paper."""
        text = f"{paper.title} {paper.abstract}".lower()

        signals = {
            "demand": self._extract_demand_signals(text, paper),
            "scarcity": self._extract_scarcity_signals(text),
            "novelty": self._extract_novelty_signals(text),
            "quality": self._extract_quality_signals(text),
            "data_efficiency": self._extract_efficiency_signals(text),
            "performance": self._extract_performance_signals(text),
            "scale": self._extract_scale_signals(text),
            "commercial": self._extract_commercial_signals(text),
            "trend": self._extract_trend_signals(paper),
            "quality_indicators": self._extract_quality_indicators(text),
            "scaling_potential": self._extract_scaling_potential(text),
        }

        return signals

    def _extract_demand_signals(self, text: str, paper: Paper) -> dict:
        """Extract demand-related signals."""
        score = 0.0
        detected = []

        # Scarcity complaints
        scarcity_keywords = self.keywords.get("scarcity", [])
        scarcity_matches = sum(1 for kw in scarcity_keywords if kw.lower() in text)
        if scarcity_matches > 0:
            score += min(scarcity_matches * 2.5, 8.0)
            detected.append("scarcity_complaint")

        # Synthetic workarounds
        synthetic_keywords = self.keywords.get("synthetic", [])
        synthetic_matches = sum(1 for kw in synthetic_keywords if kw.lower() in text)
        if synthetic_matches > 0:
            score += min(synthetic_matches * 2.0, 6.0)
            detected.append("synthetic_workaround")

        return {"score": min(score, 10.0), "detected": detected}

    def _extract_scarcity_signals(self, text: str) -> dict:
        """Extract scarcity-related signals."""
        score = 0.0
        detected = []

        # Collection costs
        cost_keywords = self.keywords.get("collection_cost", [])
        cost_matches = sum(1 for kw in cost_keywords if kw.lower() in text)
        if cost_matches > 0:
            score += min(cost_matches * 3.0, 9.0)
            detected.append("collection_cost")

        # Privacy restrictions
        privacy_keywords = self.keywords.get("privacy", [])
        privacy_matches = sum(1 for kw in privacy_keywords if kw.lower() in text)
        if privacy_matches > 0:
            score += min(privacy_matches * 3.5, 9.0)
            detected.append("privacy_restriction")

        # Dataset size mentions
        size_patterns = [
            r"only \d+[km]? samples",
            r"limited to \d+[km]? examples",
            r"small dataset",
            r"insufficient.*data",
        ]
        for pattern in size_patterns:
            if re.search(pattern, text):
                score += 3.0
                detected.append("size_limitation")
                break

        return {"score": min(score, 10.0), "detected": detected}

    def _extract_novelty_signals(self, text: str) -> dict:
        """Extract novelty-related signals."""
        score = 0.0
        detected = []

        # Novelty keywords
        novelty_keywords = self.keywords.get("novelty", [])
        novelty_matches = sum(1 for kw in novelty_keywords if kw.lower() in text)
        if novelty_matches > 0:
            score += min(novelty_matches * 2.0, 7.0)
            detected.append("novelty_markers")

        # Multimodal mentions
        if any(term in text for term in ["multimodal", "multi-modal", "cross-modal"]):
            score += 4.0
            detected.append("multimodal")

        # Emerging domains
        emerging_domains = [
            "climate",
            "pandemic",
            "drug discovery",
            "autonomous",
            "precision agriculture",
            "renewable energy",
            "carbon capture",
        ]
        for domain in emerging_domains:
            if domain in text:
                score += 3.0
                detected.append(f"emerging_{domain.replace(' ', '_')}")
                break

        return {"score": min(score, 10.0), "detected": detected}

    def _extract_quality_signals(self, text: str) -> dict:
        """Extract quality-related signals."""
        score = 0.0
        detected = []

        # Quality keywords
        quality_keywords = self.keywords.get("quality", [])
        quality_matches = sum(1 for kw in quality_keywords if kw.lower() in text)
        if quality_matches > 0:
            score += min(quality_matches * 2.5, 8.0)
            detected.append("quality_emphasis")

        # Expert involvement
        if any(term in text for term in ["expert", "specialist", "clinician", "radiologist"]):
            score += 4.0
            detected.append("expert_involvement")

        # Methodology emphasis
        methodology_terms = ["annotation protocol", "quality control", "curation process", "selection criteria"]
        if any(term in text for term in methodology_terms):
            score += 3.0
            detected.append("methodology_emphasis")

        # Quality over quantity explicit statement
        if any(phrase in text for phrase in ["quality over quantity", "carefully curated", "strategic selection"]):
            score += 4.0
            detected.append("explicit_quality_focus")

        return {"score": min(score, 10.0), "detected": detected}

    def _extract_scale_signals(self, text: str) -> dict:
        """Extract scale-related signals."""
        score = 0.0
        detected = []

        # Scale keywords
        scale_keywords = self.keywords.get("scale", [])
        scale_matches = sum(1 for kw in scale_keywords if kw.lower() in text)
        if scale_matches > 0:
            score += min(scale_matches * 3.0, 9.0)
            detected.append("scale_opportunity")

        # Pre-training mentions
        if any(term in text for term in ["pre-train", "pretrain", "foundation model", "self-supervised"]):
            score += 5.0
            detected.append("pretraining_gap")

        return {"score": min(score, 10.0), "detected": detected}

    def _extract_commercial_signals(self, text: str) -> dict:
        """Extract commercial viability signals."""
        score = 0.0
        detected = []

        # Industry keywords
        industry_keywords = self.keywords.get("industry", [])
        industry_matches = sum(1 for kw in industry_keywords if kw.lower() in text)
        if industry_matches > 0:
            score += min(industry_matches * 3.0, 9.0)
            detected.append("industry_mention")

        # Regulatory mentions
        if any(term in text for term in ["fda", "hipaa", "gdpr", "regulatory", "compliance"]):
            score += 4.0
            detected.append("regulatory_need")

        return {"score": min(score, 10.0), "detected": detected}

    def _extract_trend_signals(self, paper: Paper) -> dict:
        """Extract trend-related signals."""
        score = 0.0
        detected = []

        # Citation count (if available)
        if paper.citation_count and paper.citation_count > 50:
            score += 6.0
            detected.append("high_citation")
        elif paper.citation_count and paper.citation_count > 20:
            score += 4.0
            detected.append("moderate_citation")

        # Major venues (from source or venue field)
        major_venues = ["neurips", "icml", "iclr", "cvpr", "acl", "emnlp"]
        if paper.venue and any(venue in paper.venue.lower() for venue in major_venues):
            score += 5.0
            detected.append("major_venue")

        return {"score": min(score, 10.0), "detected": detected}

    def _extract_efficiency_signals(self, text: str) -> dict:
        """Extract data efficiency signals."""
        score = 0.0
        detected = []

        # Efficiency keywords
        efficiency_keywords = self.keywords.get("data_efficiency", [])
        efficiency_matches = sum(1 for kw in efficiency_keywords if kw.lower() in text)
        if efficiency_matches > 0:
            score += min(efficiency_matches * 3.0, 9.0)
            detected.append("efficiency_emphasis")

        # Comparative patterns (high value!)
        comparative_patterns = [
            r"(\d+)%\s*(improvement|better|gain)",
            r"only\s+\d+[km]?\s*(samples|examples)",
            r"outperform.*\d+[km]?\s*(samples|examples)",
            r"achieve.*with.*fewer",
            r"despite.*smaller",
            r"fraction of.*data",
        ]

        for pattern in comparative_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                score += 5.0
                detected.append("comparative_efficiency")
                break

        return {"score": min(score, 10.0), "detected": detected}

    def _extract_performance_signals(self, text: str) -> dict:
        """Extract performance improvement signals."""
        score = 0.0
        detected = []

        # Performance keywords
        perf_keywords = self.keywords.get("performance_impact", [])
        perf_matches = sum(1 for kw in perf_keywords if kw.lower() in text)
        if perf_matches > 0:
            score += min(perf_matches * 2.0, 6.0)
            detected.append("performance_claims")

        # Quantified improvements
        improvement_patterns = [
            r"(\d+)%\s*improvement",
            r"(\d+)%\s*better",
            r"(\d+)%\s*gain",
            r"state-of-the-art",
            r"outperform.*baseline",
        ]

        for pattern in improvement_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                score += 5.0
                detected.append("quantified_impact")
                break

        return {"score": min(score, 10.0), "detected": detected}

    def _extract_quality_indicators(self, text: str) -> dict:
        """Extract quality assurance and validation signals."""
        score = 0.0
        detected = []
        sample_phrases = []

        # Quality indicator keywords
        quality_keywords = self.keywords.get("quality_indicators", [])
        for kw in quality_keywords:
            if kw.lower() in text:
                score += 2.5
                detected.append(f"quality_kw_{kw.replace(' ', '_')}")
                # Extract sample phrase
                phrase = self._extract_sample_phrases(text, kw, context_window=30)
                if phrase:
                    sample_phrases.extend(phrase)

        # Look for inter-annotator agreement metrics
        if re.search(r"(kappa|agreement|correlation).*\d+\.\d+", text, re.IGNORECASE):
            score += 4.0
            detected.append("quantified_agreement")

        # Multi-stage validation
        if any(term in text for term in ["multi-stage", "two-stage", "validation pipeline"]):
            score += 3.0
            detected.append("multi_stage_validation")

        return {
            "score": min(score, 10.0),
            "detected": detected,
            "sample_phrases": sample_phrases[:3],  # Limit to top 3
        }

    def _extract_scaling_potential(self, text: str) -> dict:
        """Extract signals about scaling and generalization potential."""
        score = 0.0
        detected = []
        sample_phrases = []

        # Scaling keywords
        scaling_keywords = self.keywords.get("scaling_potential", [])
        for kw in scaling_keywords:
            if kw.lower() in text:
                score += 2.0
                detected.append(f"scaling_kw_{kw.replace(' ', '_')}")
                phrase = self._extract_sample_phrases(text, kw, context_window=30)
                if phrase:
                    sample_phrases.extend(phrase)

        # Look for transfer learning mentions
        if any(term in text for term in ["transfer", "fine-tune", "adapt to", "generalize"]):
            score += 4.0
            detected.append("transfer_learning")

        # Cross-domain applicability
        if re.search(r"(across|multiple|various)\s+(domains|tasks|datasets)", text, re.IGNORECASE):
            score += 5.0
            detected.append("cross_domain")

        return {
            "score": min(score, 10.0),
            "detected": detected,
            "sample_phrases": sample_phrases[:3],
        }

    def _extract_sample_phrases(self, text: str, keyword: str, context_window: int = 30) -> list[str]:
        """Extract sample phrases containing the keyword with context."""
        phrases = []
        keyword_lower = keyword.lower()

        # Find all occurrences
        start = 0
        while True:
            idx = text.find(keyword_lower, start)
            if idx == -1:
                break

            # Extract context around keyword
            context_start = max(0, idx - context_window)
            context_end = min(len(text), idx + len(keyword_lower) + context_window)
            phrase = text[context_start:context_end].strip()

            # Clean up phrase
            if context_start > 0:
                phrase = "..." + phrase
            if context_end < len(text):
                phrase = phrase + "..."

            phrases.append(phrase)
            start = idx + len(keyword_lower)

            # Limit to prevent excessive extraction
            if len(phrases) >= 3:
                break

        return phrases
