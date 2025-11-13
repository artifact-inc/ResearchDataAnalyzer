"""Base scraper interface."""

import asyncio
import logging
from abc import ABC, abstractmethod
from collections.abc import Callable
from datetime import UTC, datetime
from typing import TypeVar

import httpx

from models.paper import Paper

logger = logging.getLogger(__name__)

T = TypeVar("T")


class BaseScraper(ABC):
    """Abstract base class for all paper scrapers."""

    def __init__(self, config: dict) -> None:
        """Initialize scraper with configuration."""
        self.config = config
        self.rate_limit_seconds = config.get("rate_limit_seconds", 1)
        self.last_request_time: datetime | None = None

    async def _rate_limit(self) -> None:
        """Enforce rate limiting."""
        if self.last_request_time:
            elapsed = (datetime.now(UTC) - self.last_request_time).total_seconds()
            if elapsed < self.rate_limit_seconds:
                await asyncio.sleep(self.rate_limit_seconds - elapsed)
        self.last_request_time = datetime.now(UTC)

    async def _retry_with_backoff(self, func: Callable[[], T], max_retries: int = 3, initial_delay: float = 1.0) -> T:
        """Retry a function with exponential backoff for rate limit errors.

        Args:
            func: Async function to retry
            max_retries: Maximum number of retry attempts
            initial_delay: Initial delay in seconds (doubles each retry)

        Returns:
            Result from the function

        Raises:
            Exception: If all retries are exhausted
        """

        delay = initial_delay

        for attempt in range(max_retries + 1):
            try:
                return await func()
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429 and attempt < max_retries:
                    logger.warning(f"Rate limit hit (429), retrying in {delay}s (attempt {attempt + 1}/{max_retries})")
                    await asyncio.sleep(delay)
                    delay *= 2  # Exponential backoff
                else:
                    raise

        # Should never reach here, but satisfy type checker
        raise RuntimeError("Retry logic error")

    @abstractmethod
    async def fetch_recent_papers(self, days: int) -> list[Paper]:
        """Fetch papers from last N days."""
        pass

    @abstractmethod
    async def fetch_new_since(self, last_check: datetime) -> list[Paper]:
        """Fetch papers published since timestamp."""
        pass

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Return the name of this source."""
        pass
