"""Opportunity assessment data model."""

from dataclasses import dataclass
from datetime import datetime

from .paper import Paper


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

**Signals Detected**:
{signals_text}

---
"""

        if self.concerns:
            md += f"""## ⚠️ Concerns

{self.concerns}

---

"""

        md += f"""*Detected: {self.detected_at.strftime("%Y-%m-%d %H:%M:%S")} UTC*
*Finding ID: {self.id}*
"""
        return md
