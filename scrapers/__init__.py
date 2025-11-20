"""Paper scrapers."""

from .arxiv_scraper import ArxivScraper
from .base import BaseScraper
from .dblp_scraper import DBLPScraper
from .openalex_scraper import OpenAlexScraper
from .papers_with_code_scraper import PapersWithCodeScraper
from .semantic_scholar_scraper import SemanticScholarScraper


def create_scrapers(sources_config: dict) -> list[BaseScraper]:
    """Create enabled scrapers from configuration."""
    scrapers = []

    if sources_config.get("arxiv", {}).get("enabled", False):
        scrapers.append(ArxivScraper(sources_config["arxiv"]))

    if sources_config.get("semantic_scholar", {}).get("enabled", False):
        scrapers.append(SemanticScholarScraper(sources_config["semantic_scholar"]))

    if sources_config.get("openalex", {}).get("enabled", False):
        scrapers.append(OpenAlexScraper(sources_config["openalex"]))

    if sources_config.get("papers_with_code", {}).get("enabled", False):
        scrapers.append(PapersWithCodeScraper(sources_config["papers_with_code"]))

    if sources_config.get("dblp", {}).get("enabled", False):
        scrapers.append(DBLPScraper(sources_config["dblp"]))

    return scrapers


__all__ = [
    "BaseScraper",
    "ArxivScraper",
    "DBLPScraper",
    "OpenAlexScraper",
    "SemanticScholarScraper",
    "PapersWithCodeScraper",
    "create_scrapers",
]
