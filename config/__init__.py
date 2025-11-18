"""Configuration management."""

import json
import logging
from pathlib import Path
from typing import Any

import yaml

from research_data_analyzer.analyzers.quality_filter import FilterConfig

logger = logging.getLogger(__name__)


def load_heuristics() -> dict[str, Any]:
    """Load heuristics configuration."""
    config_path = Path(__file__).parent / "heuristics.json"
    with open(config_path) as f:
        return json.load(f)


def load_sources() -> dict[str, Any]:
    """Load sources configuration."""
    config_path = Path(__file__).parent / "sources.json"
    with open(config_path) as f:
        return json.load(f)


def load_quality_config(config_path: str | Path | None = None) -> FilterConfig:
    """Load quality filter configuration from YAML file.

    Args:
        config_path: Path to config file (default: config/quality_config.yaml)

    Returns:
        FilterConfig instance
    """
    if config_path is None:
        # Default to quality_config.yaml in same directory as this file
        config_path = Path(__file__).parent / "quality_config.yaml"
    else:
        config_path = Path(config_path)

    if not config_path.exists():
        logger.warning(f"Config file not found: {config_path}, using defaults")
        return FilterConfig()

    try:
        with open(config_path) as f:
            config_data = yaml.safe_load(f)

        quality_settings = config_data.get("quality_filter", {})

        return FilterConfig(
            enabled=quality_settings.get("enabled", True),
            min_citations_absolute=quality_settings.get("min_citations_absolute", 5),
            citation_thresholds=quality_settings.get("citation_thresholds"),
            min_author_papers=quality_settings.get("min_author_papers", 3),
            allow_unknown_citations=quality_settings.get("allow_unknown_citations", False),
        )

    except Exception as e:
        logger.error(f"Error loading config from {config_path}: {e}")
        logger.warning("Using default configuration")
        return FilterConfig()


__all__ = ["load_heuristics", "load_sources", "load_quality_config"]
