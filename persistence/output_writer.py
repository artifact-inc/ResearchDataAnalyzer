"""Output writer for findings."""

import json
import logging
from datetime import UTC, datetime
from pathlib import Path

from models.opportunity import OpportunityAssessment

logger = logging.getLogger(__name__)


class OutputWriter:
    """Write opportunity findings to files."""

    def __init__(self, base_dir: str = "./findings") -> None:
        """Initialize output writer."""
        self.base_dir = Path(base_dir)
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Create output directory structure."""
        self.base_dir.mkdir(parents=True, exist_ok=True)

        for tier in ["S", "A", "B", "C", "D"]:
            tier_dir = self.base_dir / f"tier_{tier.lower()}"
            tier_dir.mkdir(exist_ok=True)

    def write_finding(self, assessment: OpportunityAssessment) -> Path:
        """Write a finding to file."""
        # Determine output directory based on tier
        tier_dir = self.base_dir / f"tier_{assessment.tier.lower()}"

        # Create filename
        timestamp = datetime.now(UTC).strftime("%Y-%m-%d")
        safe_name = self._sanitize_filename(assessment.data_type_name)
        filename = f"{timestamp}_{safe_name}.md"

        filepath = tier_dir / filename

        # Write markdown file
        markdown = assessment.to_markdown()
        filepath.write_text(markdown, encoding="utf-8")

        # Append to index
        self._append_to_index(assessment)

        logger.info(f"[{assessment.tier}] Wrote finding: {filepath}")
        return filepath

    def _append_to_index(self, assessment: OpportunityAssessment) -> None:
        """Append finding to machine-readable index."""
        index_file = self.base_dir / "index.jsonl"

        entry = {
            "id": assessment.id,
            "tier": assessment.tier,
            "data_type_name": assessment.data_type_name,
            "value_score": assessment.value_score,
            "confidence_score": assessment.confidence_score,
            "paper_url": assessment.paper.url,
            "paper_title": assessment.paper.title,
            "detected_at": assessment.detected_at.isoformat(),
        }

        with open(index_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

    def _sanitize_filename(self, name: str) -> str:
        """Sanitize name for use in filename."""
        # Remove/replace problematic characters
        safe_name = name.lower()
        safe_name = safe_name.replace(" ", "_")
        safe_name = "".join(c for c in safe_name if c.isalnum() or c in "_-")
        return safe_name[:50]  # Limit length
