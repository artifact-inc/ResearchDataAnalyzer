"""arXiv paper scraper."""

import logging
import xml.etree.ElementTree as ET
from datetime import UTC, datetime, timedelta

import httpx

from models.paper import Paper

from .base import BaseScraper

logger = logging.getLogger(__name__)


class ArxivScraper(BaseScraper):
    """Scraper for arXiv papers."""

    @property
    def source_name(self) -> str:
        """Return source name."""
        return "arxiv"

    async def fetch_recent_papers(self, days: int) -> list[Paper]:
        """Fetch papers from last N days."""
        papers = []
        categories = self.config.get("categories", ["cs.AI"])

        for category in categories:
            logger.info(f"Fetching arXiv papers from {category} (last {days} days)")
            category_papers = await self._fetch_category_papers(category, days)
            papers.extend(category_papers)
            await self._rate_limit()

        logger.info(f"Fetched {len(papers)} papers from arXiv")
        return papers

    async def fetch_new_since(self, last_check: datetime) -> list[Paper]:
        """Fetch papers since timestamp."""

        days = (datetime.now(UTC) - last_check).days + 1
        return await self.fetch_recent_papers(days)

    async def _fetch_category_papers(self, category: str, days: int) -> list[Paper]:
        """Fetch papers for a specific category."""
        base_url = self.config["base_url"]
        max_results = 100

        query = f"cat:{category}"
        url = f"{base_url}?search_query={query}&sortBy=submittedDate&sortOrder=descending&max_results={max_results}"

        try:
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                response = await client.get(url)
                response.raise_for_status()

                return self._parse_arxiv_response(response.text, days)
        except Exception as e:
            logger.error(f"Error fetching arXiv papers for {category}: {e}")
            return []

    def _parse_arxiv_response(self, xml_text: str, days: int) -> list[Paper]:
        """Parse arXiv API XML response."""

        papers = []
        cutoff_date = datetime.now(UTC) - timedelta(days=days)

        try:
            root = ET.fromstring(xml_text)
            ns = {"atom": "http://www.w3.org/2005/Atom"}

            entries = root.findall("atom:entry", ns)
            logger.debug(f"ArXiv response contains {len(entries)} entries")
            logger.debug(f"Cutoff date for filtering: {cutoff_date}")

            for entry in entries:
                try:
                    published_str = entry.find("atom:published", ns).text
                    published_date = datetime.fromisoformat(published_str.replace("Z", "+00:00"))

                    if published_date < cutoff_date:
                        logger.debug(f"Skipping paper published {published_date} (before cutoff {cutoff_date})")
                        continue

                    logger.debug(f"Including paper published {published_date}")

                    arxiv_id = entry.find("atom:id", ns).text.split("/")[-1]
                    title = entry.find("atom:title", ns).text.strip().replace("\n", " ")
                    abstract = entry.find("atom:summary", ns).text.strip().replace("\n", " ")

                    authors = []
                    for author in entry.findall("atom:author", ns):
                        name_elem = author.find("atom:name", ns)
                        if name_elem is not None:
                            authors.append(name_elem.text)

                    url = f"https://arxiv.org/abs/{arxiv_id}"

                    paper = Paper(
                        id=f"arxiv_{arxiv_id}",
                        title=title,
                        abstract=abstract,
                        authors=authors,
                        published_date=published_date.replace(tzinfo=None),
                        source="arxiv",
                        url=url,
                    )
                    papers.append(paper)

                except Exception as e:
                    logger.warning(f"Error parsing arXiv entry: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error parsing arXiv XML: {e}")

        logger.info(f"Parsed {len(papers)} papers from arXiv response (filtered by date)")
        return papers
