"""Papers with Code scraper implementation."""

import logging
from datetime import UTC, datetime, timedelta

import httpx

from models.paper import Paper
from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class PapersWithCodeScraper(BaseScraper):
    """Scraper for Papers with Code."""

    def __init__(self, config: dict):
        super().__init__(config)
        self.base_url = config.get("base_url", "https://paperswithcode.com/api/v1")
        self.max_results = config.get("max_results_per_page", 50)

    async def fetch_recent_papers(self, days: int) -> list[Paper]:
        """Fetch papers from last N days."""
        start_date = datetime.now(UTC) - timedelta(days=days)
        return await self.fetch_new_since(start_date)

    async def fetch_new_since(self, last_check: datetime) -> list[Paper]:
        """Fetch papers published since timestamp."""
        papers = []

        try:
            await self._rate_limit()
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/papers/",
                    params={"page": 1, "items_per_page": self.max_results},
                    timeout=30.0,
                )
                response.raise_for_status()

                data = response.json()
                for item in data.get("results", []):
                    paper = self._parse_paper(item)
                    if paper and paper.published_date >= last_check:
                        papers.append(paper)

        except Exception as e:
            logger.error(f"[PapersWithCode] Error fetching papers: {e}")

        self._log_fetch(len(papers))
        return papers

    async def fetch_paper_details(self, paper_id: str) -> Paper | None:
        """Fetch full details for a specific paper."""
        await self._rate_limit()

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/papers/{paper_id}/", timeout=30.0)
                response.raise_for_status()
                return self._parse_paper(response.json())

        except Exception as e:
            logger.error(f"[PapersWithCode] Error fetching paper {paper_id}: {e}")
            return None

    def _parse_paper(self, data: dict) -> Paper | None:
        """Parse Papers with Code paper data."""
        try:
            paper_id = data.get("id", "")
            title = data.get("title", "")
            abstract = data.get("abstract", "")

            published_str = data.get("published", "")
            published_date = (
                datetime.fromisoformat(published_str.replace("Z", "+00:00")) if published_str else datetime.now(UTC)
            )

            authors_data = data.get("authors", [])
            authors = [a.get("name", "") for a in authors_data if a.get("name")]

            url = data.get("url_abs", "") or data.get("url_pdf", "")

            return Paper(
                id=f"pwc_{paper_id}",
                title=title,
                abstract=abstract,
                authors=authors,
                published_date=published_date,
                source="PapersWithCode",
                url=url,
            )

        except Exception as e:
            logger.warning(f"[PapersWithCode] Error parsing paper: {e}")
            return None
