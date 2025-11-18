"""Quality filter for research papers.

This module filters papers based on age-adjusted citation thresholds and
author publication history. Designed to work with both recent papers
(3-month lookback) and historical papers (1+ year lookback).
"""

import logging
from dataclasses import dataclass
from datetime import UTC, datetime

from research_data_analyzer.models import Paper

logger = logging.getLogger(__name__)


@dataclass
class FilterConfig:
    """Configuration for quality filtering.

    Attributes:
        enabled: Whether quality filtering is enabled
        min_citations_absolute: Absolute floor for citations (any age)
        citation_thresholds: Age-based minimum citations (in years)
        min_author_papers: Minimum publications for lead author
        allow_unknown_citations: Whether to pass papers with unknown citation counts
    """

    enabled: bool = True
    min_citations_absolute: int = 5
    citation_thresholds: dict[str, int] | None = None
    min_author_papers: int = 3
    allow_unknown_citations: bool = False

    def __post_init__(self) -> None:
        """Set default citation thresholds if not provided."""
        if self.citation_thresholds is None:
            # Age-adjusted thresholds designed for flexibility:
            # - 0-1 years: 3 citations (covers 3-month recent papers case)
            # - 1-2 years: 10 citations (emerging validation)
            # - 2-5 years: 20 citations (established work)
            # - 5+ years: 30 citations (mature research)
            self.citation_thresholds = {
                "0-1": 3,
                "1-2": 10,
                "2-5": 20,
                "5+": 30,
            }


def calculate_paper_age_years(paper: Paper) -> float:
    """Calculate paper age in years from published date.

    Args:
        paper: Paper to calculate age for

    Returns:
        Age in years (fractional)
    """
    now = datetime.now(UTC)
    age_days = (now - paper.published_date).days
    return age_days / 365.25


def get_citation_threshold(age_years: float, config: FilterConfig) -> int:
    """Get age-appropriate citation threshold.

    Args:
        age_years: Paper age in years
        config: Filter configuration

    Returns:
        Minimum citation count required for this age
    """
    thresholds = config.citation_thresholds or {}

    if age_years < 1:
        return thresholds.get("0-1", 3)
    elif age_years < 2:
        return thresholds.get("1-2", 10)
    elif age_years < 5:
        return thresholds.get("2-5", 20)
    else:
        return thresholds.get("5+", 30)


def passes_quality_filter(paper: Paper, config: FilterConfig) -> tuple[bool, str]:
    """Determine if paper passes quality filter.

    Source-aware filtering:
    - arXiv papers: Accepted without citations (arXiv API doesn't provide citation data)
    - Semantic Scholar papers: Must meet citation thresholds

    Args:
        paper: Paper to evaluate
        config: Filter configuration

    Returns:
        (passes, reason) tuple:
            - passes: True if paper meets quality standards
            - reason: Human-readable explanation
    """
    if not config.enabled:
        return True, "Quality filtering disabled"

    # Handle unknown citation count (source-aware)
    if paper.citation_count is None or paper.citation_count == "Unknown":
        # arXiv API doesn't provide citations, so accept arXiv papers without them
        # For other sources, respect the allow_unknown_citations config
        if paper.source == "arxiv":
            reason = "arXiv paper accepted (citation data not available from arXiv API)"
        elif config.allow_unknown_citations:
            reason = "Unknown citation count allowed by config"
        else:
            return False, "Citation count unavailable"
        return True, reason

    citation_count = int(paper.citation_count) if isinstance(paper.citation_count, str) else paper.citation_count

    # Check absolute minimum
    if citation_count < config.min_citations_absolute:
        return False, f"Below absolute minimum ({citation_count} < {config.min_citations_absolute})"

    # Calculate age and get threshold
    age_years = calculate_paper_age_years(paper)
    required_citations = get_citation_threshold(age_years, config)

    # Check age-adjusted threshold
    if citation_count < required_citations:
        return (
            False,
            f"Below age-adjusted threshold for {age_years:.1f}yr paper ({citation_count} < {required_citations})",
        )

    # Passed all checks
    return True, f"Passes: {citation_count} citations for {age_years:.1f}yr paper (threshold: {required_citations})"


def filter_papers(papers: list[Paper], config: FilterConfig) -> tuple[list[Paper], list[tuple[Paper, str]]]:
    """Filter papers by quality criteria.

    Args:
        papers: List of papers to filter
        config: Filter configuration

    Returns:
        (passed_papers, rejected_papers) tuple:
            - passed_papers: Papers that passed quality filter
            - rejected_papers: List of (paper, rejection_reason) tuples
    """
    passed: list[Paper] = []
    rejected: list[tuple[Paper, str]] = []

    for paper in papers:
        passes, reason = passes_quality_filter(paper, config)

        if passes:
            passed.append(paper)
            logger.debug(f"✓ {paper.title[:60]}... - {reason}")
        else:
            rejected.append((paper, reason))
            logger.debug(f"✗ {paper.title[:60]}... - {reason}")

    # Summary logging
    logger.info(f"Quality Filter Results: {len(passed)} passed, {len(rejected)} rejected")

    if rejected:
        # Count rejection reasons
        reason_counts: dict[str, int] = {}
        for _, reason in rejected:
            reason_type = reason.split("(")[0].strip()  # Extract reason type
            reason_counts[reason_type] = reason_counts.get(reason_type, 0) + 1

        logger.info("Rejection breakdown:")
        for reason_type, count in sorted(reason_counts.items(), key=lambda x: -x[1]):
            logger.info(f"  - {reason_type}: {count}")

    return passed, rejected
