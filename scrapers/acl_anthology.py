"""ACL Anthology scraper implementation (simplified placeholder)."""

import logging
from datetime import datetime

from models.paper import Paper
from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class ACLAnthologyScraper(BaseScraper):
    """Scraper for ACL Anthology (placeholder implementation)."""

    def __init__(self, config: dict):
        super().__init__(config)
        self.base_url = config.get("base_url", "https://aclanthology.org")
        self.venues = config.get("venues", ["ACL", "EMNLP", "NAACL"])

    async def fetch_recent_papers(self, days: int) -> list[Paper]:
        """Fetch papers from last N days."""
        logger.warning("[ACLAnthology] Placeholder implementation - returning empty list")
        return []

    async def fetch_new_since(self, last_check: datetime) -> list[Paper]:
        """Fetch papers published since timestamp."""
        logger.warning("[ACLAnthology] Placeholder implementation - returning empty list")
        return []

    async def fetch_paper_details(self, paper_id: str) -> Paper | None:
        """Fetch full details for a specific paper."""
        logger.warning("[ACLAnthology] Placeholder implementation - returning None")
        return None
