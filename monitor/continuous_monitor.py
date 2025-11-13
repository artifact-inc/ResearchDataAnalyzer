"""Continuous monitoring mode."""

import asyncio
import logging
from datetime import UTC, datetime, timedelta

from analyzers import SignalExtractor, ValueEvaluator
from persistence import OutputWriter

logger = logging.getLogger(__name__)


async def run_continuous_monitor(
    scrapers: list,
    signal_extractor: SignalExtractor,
    value_evaluator: ValueEvaluator,
    output_writer: OutputWriter,
    poll_interval_hours: int,
    config: dict,
) -> None:
    """Run continuous monitoring for new papers."""
    logger.info(f"Starting continuous monitoring (poll interval: {poll_interval_hours}h)")

    last_check = datetime.now(UTC) - timedelta(days=1)  # Start with last 24h

    while True:
        logger.info(f"Checking for new papers since {last_check.strftime('%Y-%m-%d %H:%M:%S')}")

        # Fetch new papers from all sources
        all_papers = []
        for scraper in scrapers:
            try:
                papers = await scraper.fetch_new_since(last_check)
                all_papers.extend(papers)
                if papers:
                    logger.info(f"Found {len(papers)} new papers from {scraper.source_name}")
            except Exception as e:
                logger.error(f"Error fetching from {scraper.source_name}: {e}")
                continue

        if not all_papers:
            logger.info("No new papers found")
        else:
            # Process new papers
            await _process_papers(
                all_papers,
                signal_extractor,
                value_evaluator,
                output_writer,
                config,
            )

            # Update last_check to newest paper date
            for paper in all_papers:
                last_check = max(last_check, paper.published_date)

        # Sleep until next poll
        logger.info(f"Sleeping for {poll_interval_hours} hours...")
        await asyncio.sleep(poll_interval_hours * 3600)


async def _process_papers(
    papers: list,
    signal_extractor: SignalExtractor,
    value_evaluator: ValueEvaluator,
    output_writer: OutputWriter,
    config: dict,
) -> None:
    """Process a batch of papers."""
    threshold = config.get("thresholds", {}).get("value_score_minimum", 6.0)

    for paper in papers:
        try:
            # Extract signals
            signals = signal_extractor.extract(paper)

            # Quick filter
            max_signal = max((s["score"] for s in signals.values()), default=0)
            if max_signal < 5.0:
                continue

            # Evaluate
            assessment = await value_evaluator.evaluate(paper, signals, config)

            if assessment and assessment.value_score >= threshold:
                output_writer.write_finding(assessment)
                logger.info(f"🔥 [{assessment.tier}] {assessment.data_type_name} (value: {assessment.value_score:.1f})")

        except Exception as e:
            logger.error(f"Error processing paper {paper.id}: {e}")
            continue
