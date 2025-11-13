"""Configuration management."""

import json
from pathlib import Path
from typing import Any


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


__all__ = ["load_heuristics", "load_sources"]
