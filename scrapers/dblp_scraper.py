"""DBLP Computer Science Bibliography scraper."""

import logging
from datetime import UTC, datetime, timedelta

import httpx

from models.paper import Paper

from .base import BaseScraper

logger = logging.getLogger(__name__)


class DBLPScraper(BaseScraper):
    """Scraper for DBLP Computer Science Bibliography."""

    @property
    def source_name(self) -> str:
        """Return source name."""
        return "dblp"

    async def fetch_recent_papers(self, days: int) -> list[Paper]:
        """Fetch papers from last N days by searching configured venues."""
        papers = []
        venues = self.config.get("venues", ["NeurIPS", "ICLR", "ICML"])

        current_year = datetime.now(UTC).year
        cutoff_date = datetime.now(UTC) - timedelta(days=days)

        years_to_search = []
        for year in range(cutoff_date.year, current_year + 1):
            years_to_search.append(year)

        logger.info(f"Fetching DBLP papers from {len(venues)} venues for years {years_to_search}")

        seen_ids = set()

        for venue in venues:
            for year in years_to_search:
                logger.debug(f"Searching DBLP: venue={venue}, year={year}")
                venue_papers = await self._search_venue(venue, year)

                for paper in venue_papers:
                    if paper.id not in seen_ids:
                        papers.append(paper)
                        seen_ids.add(paper.id)

                await self._rate_limit()

        cutoff_naive = cutoff_date.replace(tzinfo=None)
        filtered_papers = [p for p in papers if p.published_date >= cutoff_naive]

        logger.info(f"Fetched {len(filtered_papers)} papers from DBLP (deduplicated, filtered by date)")
        return filtered_papers

    async def fetch_new_since(self, last_check: datetime) -> list[Paper]:
        """Fetch papers since timestamp."""
        days = (datetime.now(UTC) - last_check).days + 1
        return await self.fetch_recent_papers(days)

    async def _search_venue(self, venue: str, year: int) -> list[Paper]:
        """Search specific venue by year."""
        base_url = self.config.get("base_url", "https://dblp.org/search/publ/api")
        max_hits = self.config.get("max_hits", 100)

        query = f"venue:{venue} year:{year}"
        url = f"{base_url}?q={query}&format=json&h={max_hits}"

        try:
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:

                async def make_request():
                    response = await client.get(url)
                    response.raise_for_status()
                    return response

                response = await self._retry_with_backoff(make_request)
                data = response.json()

                return self._parse_response(data, venue)

        except Exception as e:
            logger.error(f"Error fetching DBLP papers for {venue} {year}: {e}")
            return []

    def _parse_response(self, data: dict, venue: str) -> list[Paper]:
        """Parse DBLP API JSON response."""
        papers = []

        try:
            result = data.get("result", {})
            hits = result.get("hits", {}).get("hit", [])

            logger.debug(f"DBLP response contains {len(hits)} hits for venue {venue}")

            for hit in hits:
                try:
                    paper = self._parse_hit(hit, venue)
                    if paper:
                        papers.append(paper)
                except Exception as e:
                    logger.warning(f"Error parsing DBLP hit: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error parsing DBLP response: {e}")

        logger.debug(f"Parsed {len(papers)} papers from DBLP response")
        return papers

    def _parse_hit(self, hit: dict, venue: str) -> Paper | None:
        """Parse DBLP hit into Paper.

        Args:
            hit: DBLP API hit dictionary
            venue: Venue name for context

        Returns:
            Paper object or None if parsing fails or required fields missing
        """
        try:
            info = hit.get("info", {})

            title = info.get("title")
            year = info.get("year")
            key = info.get("key")

            if not title or not year or not key:
                logger.debug(
                    f"Skipping hit: missing required field (title={bool(title)}, year={bool(year)}, key={bool(key)})"
                )
                return None

            # Allow empty abstracts for DBLP (they rarely provide them)
            abstract = info.get("abstract", "")
            if not abstract:
                logger.debug(f"DBLP paper without abstract (expected) - including paper for metadata: '{title}'")

            authors_data = info.get("authors", {}).get("author", [])
            authors = []

            if isinstance(authors_data, dict):
                authors_data = [authors_data]

            for author in authors_data:
                if isinstance(author, dict):
                    author_name = author.get("text", "")
                elif isinstance(author, str):
                    author_name = author
                else:
                    continue

                if author_name:
                    authors.append(author_name)

            published_date = datetime(int(year), 1, 1, tzinfo=UTC).replace(tzinfo=None)

            paper_id = f"dblp_{key.replace('/', '_')}"

            url = info.get("url", f"https://dblp.org/rec/{key}")

            venue_name = info.get("venue", venue)

            paper = Paper(
                id=paper_id,
                title=title,
                abstract=abstract,
                authors=authors,
                published_date=published_date,
                source="dblp",
                url=url,
                venue=venue_name,
            )

            return paper

        except Exception as e:
            logger.warning(f"Error parsing DBLP hit: {e}")
            return None
