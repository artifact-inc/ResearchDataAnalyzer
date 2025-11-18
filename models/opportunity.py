"""Opportunity assessment data model."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from .paper import Paper


class BlockerSeverity(Enum):
    """Severity level for commercialization blockers."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class BlockerCategory(Enum):
    """Category of commercialization blocker."""

    LEGAL = "legal"  # Privacy, IP, regulatory
    TECHNICAL = "technical"  # Validation gaps, reproducibility
    MARKET = "market"  # Customer access, distribution
    ECONOMIC = "economic"  # Cost structure, pricing viability


@dataclass
class Blocker:
    """Represents a commercialization blocker."""

    category: BlockerCategory
    severity: BlockerSeverity
    description: str

    def score_cap(self: "Blocker") -> float:
        """Return maximum value_score allowed for this blocker."""
        return {BlockerSeverity.HIGH: 6.0, BlockerSeverity.MEDIUM: 7.5, BlockerSeverity.LOW: 10.0}[self.severity]


@dataclass
class UncertaintySource:
    """Represents a source of uncertainty in the assessment."""

    description: str
    penalty: float  # Points to deduct from confidence (0-10 scale)


@dataclass
class OpportunityAssessment:
    """Represents a market opportunity finding."""

    id: str
    paper: Paper
    data_type_name: str
    business_context: str
    value_score: float
    confidence_score: float
    tier: str
    signals_detected: dict[str, float]
    detected_at: datetime
    target_customers: str = ""
    market_gap: str = ""
    concerns: str = ""
    data_efficiency: float = 0.0
    source_quality: float = 0.0
    generalizability: float = 0.0

    # Data provenance fields
    dataset_description: str = ""
    data_collection_method: str = ""
    replication_feasibility: str = ""

    # Dual scoring fields
    technical_contribution_score: float = 0.0  # 0-10: Research quality/novelty
    commercial_viability_score: float = 0.0  # 0-10: Market readiness

    # Blocker and uncertainty tracking
    blockers: list[Blocker] = field(default_factory=list)
    uncertainty_sources: list[UncertaintySource] = field(default_factory=list)
    effective_value_score: float = 0.0  # value_score after blocker caps applied

    def __post_init__(self: "OpportunityAssessment") -> None:
        """Calculate effective_value_score after blocker caps."""
        if self.effective_value_score == 0.0:  # Only calculate if not already set
            self.effective_value_score = self._apply_blocker_caps()

    def _apply_blocker_caps(self: "OpportunityAssessment") -> float:
        """Apply blocker score caps to value_score."""
        if not self.blockers:
            return self.value_score

        # Find most restrictive cap from all blockers
        min_cap = min(b.score_cap() for b in self.blockers)
        return min(self.value_score, min_cap)

    def calculate_tier(self: "OpportunityAssessment") -> str:
        """Calculate tier based on effective_value_score."""
        if self.effective_value_score >= 7.5:
            return "A"
        elif self.effective_value_score >= 6.0:
            return "B"
        else:
            return "C"

    def to_markdown(self) -> str:
        """Format as markdown for text file output."""
        tier_emoji = {"S": "🔥", "A": "⭐", "B": "💎", "C": "🌱", "D": "📊"}

        signals_text = ""
        for category, score in self.signals_detected.items():
            if score >= 7.0:
                signals_text += f"- {category.replace('_', ' ').title()}: {score:.1f}\n"

        md = f"""# {tier_emoji.get(self.tier, "📊")} [Tier {self.tier}] {self.data_type_name}

**Paper**: {self.paper.url}
**Published**: {self.paper.published_date.strftime("%Y-%m-%d")}
**Citations**: {self.paper.citation_count or "Unknown"}
**Source**: {self.paper.source}

---

## 💰 Business Opportunity

{self.business_context}

**Target Customers**: {self.target_customers or "See business context"}
**Market Gap**: {self.market_gap or "See business context"}

---

## 📊 Scoring

**Value Score**: {self.value_score:.1f}/10
**Confidence**: {self.confidence_score:.1f}/10
**Tier**: {self.tier}

**Enhanced Dimensions**:
- Data Efficiency: {self.data_efficiency:.1f}/10
- Source Quality: {self.source_quality:.1f}/10
- Generalizability: {self.generalizability:.1f}/10
"""

        # Add data provenance section if any fields are populated
        if self.dataset_description or self.data_collection_method or self.replication_feasibility:
            md += "\n**Data Provenance**:\n"
            if self.dataset_description:
                md += f"- Dataset Used: {self.dataset_description}\n"
            if self.data_collection_method:
                md += f"- Collection Method: {self.data_collection_method}\n"
            if self.replication_feasibility:
                md += f"- Replication Feasibility: {self.replication_feasibility}\n"

        md += f"""
**Signals Detected**:
{signals_text}
"""

        # Add blocker information if any exist
        if self.blockers:
            md += "\n**Blockers Detected**:\n"
            for blocker in self.blockers:
                severity_emoji = {"high": "🚫", "medium": "⚠️", "low": "ℹ️"}
                emoji = severity_emoji.get(blocker.severity.value, "•")
                category = blocker.category.value.upper()
                md += f"- {emoji} [{category}] {blocker.description}\n"
            md += f"\n**Effective Score**: {self.effective_value_score:.1f}/10 (after blocker caps)\n"

        # Add dual scoring information if available
        if self.technical_contribution_score > 0.0 or self.commercial_viability_score > 0.0:
            md += "\n**Dual Scoring**:\n"
            md += f"- Technical Contribution: {self.technical_contribution_score:.1f}/10\n"
            md += f"- Commercial Viability: {self.commercial_viability_score:.1f}/10\n"

        # Add uncertainty sources if any exist
        if self.uncertainty_sources:
            md += "\n**Uncertainty Sources**:\n"
            for source in self.uncertainty_sources:
                md += f"- {source.description} (-{source.penalty:.1f} confidence)\n"

        md += "\n---\n"

        if self.concerns:
            md += f"""## ⚠️ Concerns

{self.concerns}

---

"""

        md += f"""*Detected: {self.detected_at.strftime("%Y-%m-%d %H:%M:%S")} UTC*
*Finding ID: {self.id}*
"""
        return md
