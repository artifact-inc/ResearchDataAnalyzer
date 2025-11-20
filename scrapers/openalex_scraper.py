"""OpenAlex paper scraper."""

import logging
from datetime import UTC, datetime, timedelta

import httpx

from models.paper import Paper

from .base import BaseScraper

logger = logging.getLogger(__name__)


class OpenAlexScraper(BaseScraper):
    """Scraper for OpenAlex papers."""

    @property
    def source_name(self) -> str:
        """Return source name."""
        return "openalex"

    async def fetch_recent_papers(self, days: int) -> list[Paper]:
        """Fetch papers from last N days."""
        from_date = (datetime.now(UTC) - timedelta(days=days)).strftime("%Y-%m-%d")
        filters = {"from_publication_date": from_date}
        logger.info(f"Fetching OpenAlex papers from {from_date} ({days} days)")
        papers = await self._fetch_works(filters)
        logger.info(f"Fetched {len(papers)} papers from OpenAlex")
        return papers

    async def fetch_new_since(self, last_check: datetime) -> list[Paper]:
        """Fetch papers since timestamp."""
        from_date = last_check.strftime("%Y-%m-%d")
        filters = {"from_publication_date": from_date}
        logger.info(f"Fetching OpenAlex papers since {from_date}")
        return await self._fetch_works(filters)

    def _reconstruct_abstract(self, inverted_index: dict) -> str:
        """Reconstruct abstract from inverted index.

        Args:
            inverted_index: Dictionary mapping words to position lists

        Returns:
            Reconstructed abstract text
        """
        if not inverted_index:
            return ""

        max_position = max(max(positions) for positions in inverted_index.values())
        words = [""] * (max_position + 1)

        for word, positions in inverted_index.items():
            for position in positions:
                words[position] = word

        return " ".join(words)

    async def _fetch_works(self, filters: dict) -> list[Paper]:
        """Fetch works with given filters.

        Args:
            filters: Dictionary of filter parameters

        Returns:
            List of parsed papers
        """
        base_url = self.config["base_url"]
        email = self.config.get("email", "")
        concepts = self.config.get("concepts", [])
        additional_filters = self.config.get("filters", {})

        filter_parts = [f"{k}:{v}" for k, v in filters.items()]
        filter_parts.extend([f"{k}:{v}" for k, v in additional_filters.items()])

        if concepts:
            concept_filter = "|".join(concepts)
            filter_parts.append(f"concepts.id:{concept_filter}")

        filter_string = ",".join(filter_parts)

        headers = {"User-Agent": f"ResearchDataAnalyzer/1.0 (mailto:{email})"}

        papers = []
        cursor = "*"
        per_page = 100

        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            while True:
                await self._rate_limit()

                url = f"{base_url}/works"
                params = {"filter": filter_string, "per-page": per_page, "cursor": cursor}

                try:

                    async def make_request(request_url: str = url, request_params: dict = params) -> httpx.Response:
                        response = await client.get(request_url, params=request_params, headers=headers)
                        response.raise_for_status()
                        return response

                    response = await self._retry_with_backoff(make_request)
                    data = response.json()

                    results = data.get("results", [])
                    if not results:
                        break

                    for work in results:
                        try:
                            paper = self._parse_work(work)
                            if paper:
                                papers.append(paper)
                        except Exception as e:
                            logger.warning(f"Error parsing OpenAlex work: {e}")
                            continue

                    meta = data.get("meta", {})
                    next_cursor = meta.get("next_cursor")
                    if not next_cursor:
                        break

                    cursor = next_cursor

                except Exception as e:
                    logger.error(f"Error fetching OpenAlex works: {e}")
                    break

        return papers

    def _parse_work(self, work: dict) -> Paper | None:
        """Parse OpenAlex work into Paper.

        Args:
            work: OpenAlex work dictionary

        Returns:
            Parsed Paper or None if required fields missing
        """
        title = work.get("title")
        if not title:
            logger.debug("Skipping work without title")
            return None

        abstract_inverted_index = work.get("abstract_inverted_index", {})
        abstract = self._reconstruct_abstract(abstract_inverted_index)
        if not abstract:
            logger.debug(f"Skipping work without abstract: {title}")
            return None

        work_id = work.get("id", "").split("/")[-1]
        if not work_id:
            logger.debug(f"Skipping work without ID: {title}")
            return None

        authors = []
        for authorship in work.get("authorships", []):
            author = authorship.get("author", {})
            display_name = author.get("display_name")
            if display_name:
                authors.append(display_name)

        publication_date_str = work.get("publication_date")
        if not publication_date_str:
            logger.debug(f"Skipping work without publication date: {title}")
            return None

        try:
            published_date = datetime.fromisoformat(publication_date_str)
        except ValueError:
            logger.warning(f"Invalid publication date format: {publication_date_str}")
            return None

        doi = work.get("doi")
        url = doi if doi else work.get("id", "")

        citation_count = work.get("cited_by_count")

        primary_location = work.get("primary_location", {})
        source = primary_location.get("source", {})
        venue = source.get("display_name")

        return Paper(
            id=f"openalex_{work_id}",
            title=title,
            abstract=abstract,
            authors=authors,
            published_date=published_date.replace(tzinfo=None),
            source="openalex",
            url=url,
            citation_count=citation_count,
            venue=venue,
        )
