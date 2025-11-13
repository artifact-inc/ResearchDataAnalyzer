"""ArXiv scraper implementation."""

import logging
import re
import xml.etree.ElementTree as ET
from datetime import UTC, datetime, timedelta
from urllib.parse import quote_plus

import httpx

from models.paper import Paper
from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class ArxivScraper(BaseScraper):
    """Scraper for arXiv papers."""

    def __init__(self, config: dict):
        super().__init__(config)
        self.base_url = config.get("base_url", "http://export.arxiv.org/api/query")
        self.categories = config.get("categories", ["cs.AI", "cs.CL", "cs.CV", "cs.LG"])
        self.max_results = config.get("max_results_per_query", 100)

    async def fetch_recent_papers(self, days: int) -> list[Paper]:
        """Fetch papers from last N days."""
        start_date = datetime.now(UTC) - timedelta(days=days)
        return await self.fetch_new_since(start_date)

    async def fetch_new_since(self, last_check: datetime) -> list[Paper]:
        """Fetch papers published since timestamp."""
        papers = []

        for category in self.categories:
            await self._rate_limit()
            try:
                category_papers = await self._fetch_category(category, last_check)
                papers.extend(category_papers)
                logger.info(f"[ArXiv] Fetched {len(category_papers)} papers from {category}")
            except Exception as e:
                logger.error(f"[ArXiv] Error fetching {category}: {e}")

        self._log_fetch(len(papers), f"across {len(self.categories)} categories")
        return papers

    async def fetch_paper_details(self, paper_id: str) -> Paper | None:
        """Fetch full details for a specific paper."""
        await self._rate_limit()

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}?id_list={paper_id}", timeout=30.0)
                response.raise_for_status()

                papers = self._parse_response(response.text)
                return papers[0] if papers else None

        except Exception as e:
            logger.error(f"[ArXiv] Error fetching paper {paper_id}: {e}")
            return None

    async def _fetch_category(self, category: str, start_date: datetime) -> list[Paper]:
        """Fetch papers for a specific category."""
        query = f"cat:{category}"
        url = (
            f"{self.base_url}?search_query={quote_plus(query)}&start=0"
            f"&max_results={self.max_results}&sortBy=submittedDate&sortOrder=descending"
        )

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=30.0)
                response.raise_for_status()

                papers = self._parse_response(response.text)

                return [p for p in papers if p.published_date >= start_date]

        except Exception as e:
            logger.error(f"[ArXiv] Error fetching category {category}: {e}")
            return []

    def _parse_response(self, xml_content: str) -> list[Paper]:
        """Parse arXiv API XML response."""
        papers = []

        try:
            root = ET.fromstring(xml_content)
            ns = {"atom": "http://www.w3.org/2005/Atom"}

            for entry in root.findall("atom:entry", ns):
                try:
                    paper = self._parse_entry(entry, ns)
                    if paper:
                        papers.append(paper)
                except Exception as e:
                    logger.warning(f"[ArXiv] Error parsing entry: {e}")

        except Exception as e:
            logger.error(f"[ArXiv] Error parsing XML response: {e}")

        return papers

    def _parse_entry(self, entry: ET.Element, ns: dict) -> Paper | None:
        """Parse a single arXiv entry."""
        try:
            arxiv_id = entry.find("atom:id", ns)
            if arxiv_id is None or not arxiv_id.text:
                return None

            paper_id = arxiv_id.text.split("/")[-1]

            title_elem = entry.find("atom:title", ns)
            title = self._clean_text(title_elem.text) if title_elem is not None else ""

            summary_elem = entry.find("atom:summary", ns)
            abstract = self._clean_text(summary_elem.text) if summary_elem is not None else ""

            published_elem = entry.find("atom:published", ns)
            published_date = (
                datetime.fromisoformat(published_elem.text.replace("Z", "+00:00"))
                if published_elem is not None
                else datetime.now(UTC)
            )

            authors = []
            for author in entry.findall("atom:author", ns):
                name_elem = author.find("atom:name", ns)
                if name_elem is not None and name_elem.text:
                    authors.append(name_elem.text)

            url = arxiv_id.text if arxiv_id is not None else ""

            dataset_mentions = self._extract_dataset_mentions(title, abstract)

            return Paper(
                id=f"arxiv_{paper_id}",
                title=title,
                abstract=abstract,
                authors=authors,
                published_date=published_date,
                source="arXiv",
                url=url,
                dataset_mentions=dataset_mentions,
            )

        except Exception as e:
            logger.warning(f"[ArXiv] Error parsing entry details: {e}")
            return None

    def _clean_text(self, text: str) -> str:
        """Clean whitespace from text."""
        return " ".join(text.split())

    def _extract_dataset_mentions(self, title: str, abstract: str) -> list[str]:
        """Extract dataset mentions from title and abstract."""
        text = f"{title} {abstract}".lower()
        datasets = []

        dataset_patterns = [
            r"\b([A-Z][A-Za-z0-9\-]+(?:\s+[A-Z][A-Za-z0-9\-]+)*)\s+dataset\b",
            r"\bdataset[s]?\s+(?:called|named)\s+([A-Z][A-Za-z0-9\-]+)\b",
            r"\b(ImageNet|COCO|SQuAD|GLUE|SuperGLUE|CIFAR|MNIST)\b",
        ]

        for pattern in dataset_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                dataset_name = match.group(1) if match.lastindex else match.group(0)
                if dataset_name and len(dataset_name) > 2:
                    datasets.append(dataset_name)

        return list(set(datasets))
