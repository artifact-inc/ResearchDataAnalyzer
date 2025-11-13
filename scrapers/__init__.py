"""Paper scrapers."""

from .arxiv_scraper import ArxivScraper
from .base import BaseScraper
from .semantic_scholar_scraper import SemanticScholarScraper


def create_scrapers(sources_config: dict) -> list[BaseScraper]:
    """Create enabled scrapers from configuration."""
    scrapers = []

    if sources_config.get("arxiv", {}).get("enabled", False):
        scrapers.append(ArxivScraper(sources_config["arxiv"]))

    if sources_config.get("semantic_scholar", {}).get("enabled", False):
        scrapers.append(SemanticScholarScraper(sources_config["semantic_scholar"]))

    return scrapers


__all__ = ["BaseScraper", "ArxivScraper", "SemanticScholarScraper", "create_scrapers"]
