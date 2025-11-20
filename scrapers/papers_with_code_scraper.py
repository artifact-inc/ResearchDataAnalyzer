"""Papers with Code API scraper."""

import logging
import os
from datetime import UTC, datetime, timedelta
from functools import partial
from json import JSONDecodeError

import httpx

from models.paper import Paper

from .base import BaseScraper

logger = logging.getLogger(__name__)


class PapersWithCodeScraper(BaseScraper):
    """Scraper for Papers with Code API."""

    @property
    def source_name(self) -> str:
        """Return source name."""
        return "papers_with_code"

    async def fetch_recent_papers(self, days: int) -> list[Paper]:
        """Fetch papers from last N days."""
        logger.info(f"Fetching Papers with Code papers (last {days} days)")

        cutoff_date = datetime.now(UTC) - timedelta(days=days)
        all_papers = []

        try:
            # Fetch papers in pages
            page = 1
            max_pages = self.config.get("max_pages", 10)
            items_per_page = self.config.get("max_results_per_page", 50)

            while page <= max_pages:
                papers = await self._fetch_page(page, items_per_page, cutoff_date)

                if not papers:
                    break

                all_papers.extend(papers)

                # If we got fewer papers than requested, we've reached the end
                if len(papers) < items_per_page:
                    break

                page += 1
                await self._rate_limit()

        except Exception as e:
            logger.error(f"Error fetching Papers with Code papers: {e}")

        logger.info(f"Fetched {len(all_papers)} papers from Papers with Code")
        return all_papers

    async def fetch_new_since(self, last_check: datetime) -> list[Paper]:
        """Fetch papers since timestamp."""
        days = (datetime.now(UTC) - last_check).days + 1
        return await self.fetch_recent_papers(days)

    async def _fetch_from_api(self, url: str) -> dict:
        """Fetch data from Papers with Code API."""
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            headers = {}
            api_key = os.getenv("PAPERS_WITH_CODE_API_KEY")
            if api_key:
                headers["Authorization"] = f"Token {api_key}"
                logger.debug("Using Papers with Code API key for authentication")
            else:
                logger.debug(
                    "No PAPERS_WITH_CODE_API_KEY found. API may be rate-limited or return HTML instead of JSON."
                )

            response = await client.get(url, headers=headers)
            response.raise_for_status()

            content_type = response.headers.get("content-type", "")
            if "application/json" not in content_type:
                error_preview = response.text[:500]
                logger.error(f"Expected JSON, got '{content_type}'. Response preview: {error_preview}")
                if "text/html" in content_type:
                    logger.error(
                        "API returned HTML instead of JSON. "
                        "This likely means authentication is required. "
                        "Get an API key from https://paperswithcode.com/api/v1/docs/ "
                        "and set PAPERS_WITH_CODE_API_KEY environment variable."
                    )
                raise ValueError(
                    f"API returned {content_type} instead of JSON. May require API key for authentication."
                )

            try:
                return response.json()
            except JSONDecodeError as e:
                error_preview = response.text[:500]
                logger.error(f"Failed to decode JSON response: {e}. Response preview: {error_preview}")
                raise ValueError(
                    f"Invalid JSON response from API: {e}. Response may be malformed or incomplete."
                ) from e

    async def _fetch_page(self, page: int, items_per_page: int, cutoff_date: datetime) -> list[Paper]:
        """Fetch a single page of papers."""
        base_url = self.config["base_url"]
        url = f"{base_url}/papers/?page={page}&items_per_page={items_per_page}"

        try:
            fetch_func = partial(self._fetch_from_api, url)
            data = await self._retry_with_backoff(fetch_func)

            papers = self._parse_papers_response(data, cutoff_date)
            return papers

        except Exception as e:
            logger.error(f"Error fetching page {page}: {e}")
            return []

    async def fetch_paper_details(self, paper_id: str) -> dict | None:
        """Fetch detailed information for a specific paper."""
        base_url = self.config["base_url"]
        url = f"{base_url}/papers/{paper_id}/"

        try:
            fetch_func = partial(self._fetch_from_api, url)
            data = await self._retry_with_backoff(fetch_func)
            await self._rate_limit()
            return data

        except Exception as e:
            logger.error(f"Error fetching paper details for {paper_id}: {e}")
            return None

    async def fetch_datasets(self, paper_id: str) -> list[dict]:
        """Fetch datasets associated with a paper."""
        if not self.config.get("include_datasets", True):
            return []

        base_url = self.config["base_url"]
        url = f"{base_url}/papers/{paper_id}/datasets/"

        try:
            fetch_func = partial(self._fetch_from_api, url)
            data = await self._retry_with_backoff(fetch_func)
            await self._rate_limit()

            datasets = []
            for item in data.get("results", []):
                datasets.append(
                    {
                        "name": item.get("dataset", {}).get("name", ""),
                        "url": item.get("dataset", {}).get("url", ""),
                    }
                )

            return datasets

        except Exception as e:
            logger.error(f"Error fetching datasets for {paper_id}: {e}")
            return []

    async def fetch_benchmarks(self, paper_id: str) -> list[dict]:
        """Fetch benchmarks/results associated with a paper."""
        if not self.config.get("include_benchmarks", True):
            return []

        base_url = self.config["base_url"]
        url = f"{base_url}/papers/{paper_id}/results/"

        try:
            fetch_func = partial(self._fetch_from_api, url)
            data = await self._retry_with_backoff(fetch_func)
            await self._rate_limit()

            benchmarks = []
            for item in data.get("results", []):
                benchmarks.append(
                    {
                        "task": item.get("task", ""),
                        "dataset": item.get("dataset", ""),
                        "metrics": item.get("metrics", {}),
                    }
                )

            return benchmarks

        except Exception as e:
            logger.error(f"Error fetching benchmarks for {paper_id}: {e}")
            return []

    def _parse_papers_response(self, data: dict, cutoff_date: datetime) -> list[Paper]:
        """Parse Papers with Code API response."""
        papers = []

        for item in data.get("results", []):
            try:
                # Parse publication date
                pub_date_str = item.get("published")
                if not pub_date_str:
                    continue

                # Handle date format: "2024-01-15T00:00:00Z"
                published_date = datetime.fromisoformat(pub_date_str.replace("Z", "+00:00"))

                # Filter by cutoff date
                if published_date < cutoff_date:
                    continue

                # Extract paper information
                paper_id = item.get("id", "")
                title = item.get("title", "")
                abstract = item.get("abstract", "")

                if not abstract:
                    continue  # Skip papers without abstracts

                # Parse authors
                authors = []
                for author in item.get("authors", []):
                    if isinstance(author, dict):
                        name = author.get("name", "")
                    else:
                        name = str(author)
                    if name:
                        authors.append(name)

                # Build URL
                url = item.get("url_abs", "")
                if not url:
                    # Fallback to arXiv URL if available
                    arxiv_id = item.get("arxiv_id", "")
                    if arxiv_id:
                        url = f"https://arxiv.org/abs/{arxiv_id}"
                    else:
                        url = f"https://paperswithcode.com/paper/{paper_id}"

                # Create paper object
                paper = Paper(
                    id=f"pwc_{paper_id}",
                    title=title,
                    abstract=abstract,
                    authors=authors,
                    published_date=published_date.replace(tzinfo=None),
                    source="papers_with_code",
                    url=url,
                )
                papers.append(paper)

            except Exception as e:
                logger.warning(f"Error parsing Papers with Code entry: {e}")
                continue

        logger.debug(f"Parsed {len(papers)} papers from response (filtered by date)")
        return papers
