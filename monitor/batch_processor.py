"""Batch processing mode."""

import logging

from research_data_analyzer.analyzers import SignalExtractor, ValueEvaluator
from research_data_analyzer.analyzers.quality_filter import FilterConfig, filter_papers
from research_data_analyzer.persistence import OutputWriter

logger = logging.getLogger(__name__)


async def run_batch_analysis(
    scrapers: list,
    signal_extractor: SignalExtractor,
    value_evaluator: ValueEvaluator,
    output_writer: OutputWriter,
    lookback_days: int,
    config: dict,
    quality_config: FilterConfig,
) -> None:
    """Run one-time batch analysis of recent papers."""
    logger.info(f"Starting batch analysis (lookback: {lookback_days} days)")

    # Fetch from all sources
    all_papers = []
    for scraper in scrapers:
        try:
            logger.info(f"Fetching papers from {scraper.source_name}...")
            papers = await scraper.fetch_recent_papers(lookback_days)
            all_papers.extend(papers)
            logger.info(f"Fetched {len(papers)} papers from {scraper.source_name}")
        except Exception as e:
            logger.error(f"Error fetching from {scraper.source_name}: {e}")
            continue

    # Deduplicate by paper ID
    unique_papers = _deduplicate_papers(all_papers)
    logger.info(f"Total unique papers: {len(unique_papers)}")

    # Apply quality filter
    logger.info("=" * 60)
    logger.info("Applying quality filter...")
    filtered_papers, rejected_papers = filter_papers(unique_papers, quality_config)
    logger.info(f"Quality filter: {len(filtered_papers)} passed, {len(rejected_papers)} rejected")
    logger.info("=" * 60)

    # Process each paper
    threshold = config.get("thresholds", {}).get("value_score_minimum", 6.0)
    findings_count = 0

    for i, paper in enumerate(filtered_papers, 1):
        logger.info(f"Processing paper {i}/{len(filtered_papers)}: {paper.title[:60]}...")

        try:
            # Extract signals
            signals = signal_extractor.extract(paper)

            # Check if any strong signals detected
            max_signal = max((s["score"] for s in signals.values()), default=0)
            if max_signal < 5.0:
                logger.debug(f"Skipping paper (weak signals): {paper.title[:60]}")
                continue

            # Evaluate with AI
            assessment = await value_evaluator.evaluate(paper, signals, config)

            if not assessment:
                logger.warning(f"Failed to evaluate paper: {paper.title[:60]}")
                continue

            # Save if meets threshold
            if assessment.value_score >= threshold:
                output_writer.write_finding(assessment)
                findings_count += 1
                logger.info(
                    f"🔥 [{assessment.tier}] {assessment.data_type_name} "
                    f"(value: {assessment.value_score:.1f}, confidence: {assessment.confidence_score:.1f})"
                )
            else:
                logger.debug(f"Below threshold ({assessment.value_score:.1f} < {threshold}): {paper.title[:60]}")

        except Exception as e:
            logger.error(f"Error processing paper {paper.id}: {e}")
            continue

    logger.info(f"Batch analysis complete. Found {findings_count} opportunities.")


def _deduplicate_papers(papers: list) -> list:
    """Deduplicate papers by ID."""
    seen_ids = set()
    unique = []

    for paper in papers:
        if paper.id not in seen_ids:
            seen_ids.add(paper.id)
            unique.append(paper)

    return unique
