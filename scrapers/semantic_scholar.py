"""Semantic Scholar scraper implementation."""

import logging
import os
from datetime import UTC, datetime, timedelta

import httpx

from models.paper import Paper
from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class SemanticScholarScraper(BaseScraper):
    """Scraper for Semantic Scholar API."""

    def __init__(self, config: dict):
        super().__init__(config)
        self.base_url = config.get("base_url", "https://api.semanticscholar.org/graph/v1")
        self.fields = config.get(
            "fields",
            [
                "title",
                "abstract",
                "year",
                "authors",
                "citationCount",
                "url",
                "venue",
                "publicationDate",
            ],
        )
        self.search_fields = config.get("search_fields", ["machine learning"])
        self.api_key = os.getenv("SEMANTIC_SCHOLAR_API_KEY")

    async def fetch_recent_papers(self, days: int) -> list[Paper]:
        """Fetch papers from last N days."""
        start_date = datetime.now(UTC) - timedelta(days=days)
        return await self.fetch_new_since(start_date)

    async def fetch_new_since(self, last_check: datetime) -> list[Paper]:
        """Fetch papers published since timestamp."""
        papers = []

        for field in self.search_fields[:3]:
            await self._rate_limit()
            try:
                field_papers = await self._search_papers(field, last_check)
                papers.extend(field_papers)
                logger.info(f"[SemanticScholar] Fetched {len(field_papers)} papers for '{field}'")
            except Exception as e:
                logger.error(f"[SemanticScholar] Error searching '{field}': {e}")

        self._log_fetch(len(papers))
        return papers

    async def fetch_paper_details(self, paper_id: str) -> Paper | None:
        """Fetch full details for a specific paper."""
        await self._rate_limit()

        headers = {}
        if self.api_key:
            headers["x-api-key"] = self.api_key

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/paper/{paper_id}",
                    params={"fields": ",".join(self.fields)},
                    headers=headers,
                    timeout=30.0,
                )
                response.raise_for_status()
                return self._parse_paper(response.json())

        except Exception as e:
            logger.error(f"[SemanticScholar] Error fetching paper {paper_id}: {e}")
            return None

    async def _search_papers(self, query: str, start_date: datetime) -> list[Paper]:
        """Search papers by query."""
        headers = {}
        if self.api_key:
            headers["x-api-key"] = self.api_key

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/paper/search",
                    params={
                        "query": query,
                        "fields": ",".join(self.fields),
                        "limit": 100,
                    },
                    headers=headers,
                    timeout=30.0,
                )
                response.raise_for_status()

                data = response.json()
                papers = []

                for item in data.get("data", []):
                    paper = self._parse_paper(item)
                    if paper and paper.published_date >= start_date:
                        papers.append(paper)

                return papers

        except Exception as e:
            logger.error(f"[SemanticScholar] Error searching papers: {e}")
            return []

    def _parse_paper(self, data: dict) -> Paper | None:
        """Parse Semantic Scholar paper data."""
        try:
            paper_id = data.get("paperId", "")
            title = data.get("title", "")
            abstract = data.get("abstract", "")

            pub_date_str = data.get("publicationDate", "")
            if pub_date_str:
                try:
                    published_date = datetime.fromisoformat(pub_date_str)
                except ValueError:
                    year = data.get("year")
                    published_date = datetime(year, 1, 1, tzinfo=UTC) if year else datetime.now(UTC)
            else:
                published_date = datetime.now(UTC)

            authors_data = data.get("authors", [])
            authors = [a.get("name", "") for a in authors_data if a.get("name")]

            url = data.get("url", "") or f"https://semanticscholar.org/paper/{paper_id}"
            citation_count = data.get("citationCount")
            venue = data.get("venue", "")

            return Paper(
                id=f"s2_{paper_id}",
                title=title,
                abstract=abstract,
                authors=authors,
                published_date=published_date,
                source="SemanticScholar",
                url=url,
                citation_count=citation_count,
                venue=venue,
            )

        except Exception as e:
            logger.warning(f"[SemanticScholar] Error parsing paper: {e}")
            return None
