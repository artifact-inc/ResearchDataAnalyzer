"""Semantic Scholar API scraper."""

import logging
import os
from datetime import UTC, datetime, timedelta
from functools import partial

import httpx

from models.paper import Paper

from .base import BaseScraper

logger = logging.getLogger(__name__)


class SemanticScholarScraper(BaseScraper):
    """Scraper for Semantic Scholar API."""

    @property
    def source_name(self) -> str:
        """Return source name."""
        return "semantic_scholar"

    async def fetch_recent_papers(self, days: int) -> list[Paper]:
        """Fetch papers from last N days."""
        logger.info(f"Fetching Semantic Scholar papers (last {days} days)")

        # Semantic Scholar search with date filtering
        year = datetime.now(UTC).year  # FIX: Use current year, not cutoff year

        papers = await self._search_papers(year, days)

        logger.info(f"Fetched {len(papers)} papers from Semantic Scholar")
        return papers

    async def fetch_new_since(self, last_check: datetime) -> list[Paper]:
        """Fetch papers since timestamp."""
        days = (datetime.now(UTC) - last_check).days + 1
        return await self.fetch_recent_papers(days)

    async def _fetch_from_api(self, url: str, headers: dict) -> dict:
        """Fetch data from Semantic Scholar API."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.json()

    async def _search_papers(self, year: int, days: int) -> list[Paper]:
        """Search for recent AI/ML papers."""
        base_url = self.config["base_url"]
        fields = ",".join(self.config["fields"])

        # Search for AI/ML papers
        queries = [
            "machine learning dataset",
            "deep learning data",
            "artificial intelligence training",
            "neural network benchmark",
        ]

        all_papers = []
        cutoff_date = datetime.now(UTC) - timedelta(days=days)

        headers = {}
        api_key = os.getenv("SEMANTIC_SCHOLAR_API_KEY")
        if api_key:
            headers["x-api-key"] = api_key

        for query in queries:
            try:
                url = f"{base_url}/paper/search?query={query}&year={year}&fields={fields}&limit=50"

                # Retry on rate limit errors using partial to bind loop variables
                fetch_func = partial(self._fetch_from_api, url, headers)
                data = await self._retry_with_backoff(fetch_func)
                papers = self._parse_semantic_scholar_response(data, cutoff_date)
                all_papers.extend(papers)

                await self._rate_limit()

            except Exception as e:
                logger.error(f"Error searching Semantic Scholar for '{query}': {e}")
                continue

        # Deduplicate by paper ID
        seen_ids = set()
        unique_papers = []
        for paper in all_papers:
            if paper.id not in seen_ids:
                seen_ids.add(paper.id)
                unique_papers.append(paper)

        return unique_papers

    def _parse_semantic_scholar_response(self, data: dict, cutoff_date: datetime) -> list[Paper]:
        """Parse Semantic Scholar API response."""
        papers = []

        for item in data.get("data", []):
            try:
                if not item.get("year"):
                    continue

                # Approximate publication date from year
                pub_year = item["year"]
                published_date = datetime(pub_year, 6, 15, tzinfo=UTC)  # Approximate mid-year

                if published_date < cutoff_date:
                    continue

                paper_id = item.get("paperId", "")
                title = item.get("title", "")
                abstract = item.get("abstract", "")

                if not abstract:
                    continue  # Skip papers without abstracts

                authors = []
                for author in item.get("authors", []):
                    if "name" in author:
                        authors.append(author["name"])

                citation_count = item.get("citationCount", 0)

                # Build URL
                external_ids = item.get("externalIds", {})
                url = item.get("url", "")
                if not url and "ArXiv" in external_ids:
                    url = f"https://arxiv.org/abs/{external_ids['ArXiv']}"
                elif not url:
                    url = f"https://www.semanticscholar.org/paper/{paper_id}"

                paper = Paper(
                    id=f"s2_{paper_id}",
                    title=title,
                    abstract=abstract,
                    authors=authors,
                    published_date=published_date,
                    source="semantic_scholar",
                    url=url,
                    citation_count=citation_count,
                )
                papers.append(paper)

            except Exception as e:
                logger.warning(f"Error parsing Semantic Scholar entry: {e}")
                continue

        return papers
