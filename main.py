"""Main entry point for Research Data Landscape Analyzer."""

import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from research_data_analyzer.analyzers import SignalExtractor, ValueEvaluator
from research_data_analyzer.config import load_heuristics, load_quality_config, load_sources
from research_data_analyzer.monitor import run_batch_analysis, run_continuous_monitor
from research_data_analyzer.persistence import OutputWriter
from research_data_analyzer.scrapers import create_scrapers


def setup_logging(level: str = "INFO") -> None:
    """Configure logging."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("research_analyzer.log"),
        ],
    )


async def main() -> None:
    """Main entry point."""
    # Load environment variables
    load_dotenv()

    # Parse arguments
    parser = argparse.ArgumentParser(
        description="Research Data Landscape Analyzer - Identify dataset creation opportunities"
    )
    parser.add_argument(
        "--mode",
        choices=["batch", "monitor"],
        default=os.getenv("MODE", "batch"),
        help="Operating mode: batch (one-time scan) or monitor (continuous)",
    )
    parser.add_argument(
        "--lookback-days",
        type=int,
        default=int(os.getenv("LOOKBACK_DAYS", "90")),
        help="Number of days to look back for batch mode",
    )
    parser.add_argument(
        "--poll-interval-hours",
        type=int,
        default=int(os.getenv("POLL_INTERVAL_HOURS", "24")),
        help="Polling interval in hours for monitor mode",
    )
    parser.add_argument(
        "--findings-dir",
        type=str,
        default=os.getenv("FINDINGS_DIR", "./findings"),
        help="Output directory for findings",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default=os.getenv("LOG_LEVEL", "INFO"),
        help="Log level (DEBUG, INFO, WARNING, ERROR)",
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)

    logger.info("=" * 60)
    logger.info("Research Data Landscape Analyzer")
    logger.info("=" * 60)
    logger.info(f"Mode: {args.mode}")
    logger.info(f"Findings directory: {args.findings_dir}")

    # Load configurations
    try:
        heuristics = load_heuristics()
        sources = load_sources()
        quality_config = load_quality_config()
        logger.info("Loaded configurations")
        logger.info(f"Quality filter: {'enabled' if quality_config.enabled else 'disabled'}")
    except Exception as e:
        logger.error(f"Failed to load configurations: {e}")
        sys.exit(1)

    # Initialize components
    try:
        scrapers = create_scrapers(sources)
        logger.info(f"Initialized {len(scrapers)} scrapers")

        signal_extractor = SignalExtractor(heuristics)
        logger.info("Initialized signal extractor")

        value_evaluator = ValueEvaluator(heuristics)
        logger.info("Initialized value evaluator")

        output_writer = OutputWriter(args.findings_dir)
        logger.info("Initialized output writer")

    except Exception as e:
        logger.error(f"Failed to initialize components: {e}")
        sys.exit(1)

    # Run appropriate mode
    try:
        if args.mode == "batch":
            logger.info(f"Starting batch analysis (lookback: {args.lookback_days} days)")
            await run_batch_analysis(
                scrapers=scrapers,
                signal_extractor=signal_extractor,
                value_evaluator=value_evaluator,
                output_writer=output_writer,
                lookback_days=args.lookback_days,
                config=heuristics,
                quality_config=quality_config,
            )
        else:  # monitor mode
            logger.info(f"Starting continuous monitoring (interval: {args.poll_interval_hours}h)")
            await run_continuous_monitor(
                scrapers=scrapers,
                signal_extractor=signal_extractor,
                value_evaluator=value_evaluator,
                output_writer=output_writer,
                poll_interval_hours=args.poll_interval_hours,
                config=heuristics,
            )

    except KeyboardInterrupt:
        logger.info("Received interrupt signal, shutting down...")
    except Exception as e:
        logger.error(f"Error during execution: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
