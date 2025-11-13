"""OpenReview scraper implementation (simplified placeholder)."""

import logging
from datetime import datetime

from models.paper import Paper
from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class OpenReviewScraper(BaseScraper):
    """Scraper for OpenReview (placeholder implementation)."""

    def __init__(self, config: dict):
        super().__init__(config)
        self.base_url = config.get("base_url", "https://api.openreview.net")
        self.venues = config.get("venues", ["ICLR", "NeurIPS"])

    async def fetch_recent_papers(self, days: int) -> list[Paper]:
        """Fetch papers from last N days."""
        logger.warning("[OpenReview] Placeholder implementation - returning empty list")
        return []

    async def fetch_new_since(self, last_check: datetime) -> list[Paper]:
        """Fetch papers published since timestamp."""
        logger.warning("[OpenReview] Placeholder implementation - returning empty list")
        return []

    async def fetch_paper_details(self, paper_id: str) -> Paper | None:
        """Fetch full details for a specific paper."""
        logger.warning("[OpenReview] Placeholder implementation - returning None")
        return None
