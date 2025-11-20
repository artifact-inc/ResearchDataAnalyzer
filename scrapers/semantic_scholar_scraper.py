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

        # Calculate which years to search based on lookback period
        cutoff_date = datetime.now(UTC) - timedelta(days=days)
        current_year = datetime.now(UTC).year
        cutoff_year = cutoff_date.year

        # Search both years if lookback spans multiple years
        years_to_search = [current_year]
        if cutoff_year != current_year:
            years_to_search.insert(0, cutoff_year)  # Add earlier year first
            logger.info(f"Lookback spans multiple years: searching {cutoff_year} and {current_year}")

        # Search all relevant years
        all_papers = []
        for year in years_to_search:
            papers = await self._search_papers(year, days)
            all_papers.extend(papers)

        # Deduplicate across years
        seen_ids = set()
        unique_papers = []
        for paper in all_papers:
            if paper.id not in seen_ids:
                seen_ids.add(paper.id)
                unique_papers.append(paper)

        logger.info(f"Fetched {len(unique_papers)} papers from Semantic Scholar")
        return unique_papers

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

        # Search for dataset-focused papers
        queries = [
            "machine learning dataset release",
            "benchmark dataset evaluation",
            "training data open source",
            "multimodal dataset collection",
            "annotated dataset computer vision",
            "natural language dataset corpus",
        ]

        logger.info(f"Searching Semantic Scholar with {len(queries)} queries")
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

                # Use start of year instead of mid-year approximation
                pub_year = item["year"]
                published_date = datetime(pub_year, 1, 1, tzinfo=UTC)

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
