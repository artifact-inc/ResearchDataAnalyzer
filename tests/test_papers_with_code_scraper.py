"""Tests for Papers with Code scraper."""

import os
from datetime import UTC, datetime
from json import JSONDecodeError
from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest

from scrapers.papers_with_code_scraper import PapersWithCodeScraper


class TestPapersWithCodeScraper:
    """Tests for Papers with Code scraper."""

    @pytest.fixture
    def scraper(self) -> PapersWithCodeScraper:
        """Create PapersWithCodeScraper instance."""
        config = {
            "rate_limit_seconds": 1,
            "base_url": "https://paperswithcode.com/api/v1",
            "max_results_per_page": 50,
            "max_pages": 10,
            "include_datasets": True,
            "include_benchmarks": True,
        }
        return PapersWithCodeScraper(config)

    @pytest.mark.asyncio
    async def test_source_name(self, scraper: PapersWithCodeScraper) -> None:
        """Test source_name property returns correct lowercase format."""
        assert scraper.source_name == "papers_with_code"

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Integration test - requires full HTTP client mocking")
    async def test_fetch_recent_papers_success(self, scraper: PapersWithCodeScraper) -> None:
        """Test successful Papers with Code paper fetching."""
        sample_response = {
            "count": 2,
            "next": None,
            "previous": None,
            "results": [
                {
                    "id": "paper-1",
                    "title": "Test Paper 1",
                    "abstract": "This is a test abstract for paper 1",
                    "published": "2024-11-15T00:00:00Z",
                    "authors": [{"name": "Author One"}, {"name": "Author Two"}],
                    "url_abs": "https://arxiv.org/abs/2411.12345",
                    "arxiv_id": "2411.12345",
                },
                {
                    "id": "paper-2",
                    "title": "Test Paper 2",
                    "abstract": "This is a test abstract for paper 2",
                    "published": "2024-11-16T00:00:00Z",
                    "authors": [{"name": "Author Three"}],
                    "url_abs": "https://arxiv.org/abs/2411.54321",
                    "arxiv_id": "2411.54321",
                },
            ],
        }

        with patch("httpx.AsyncClient.get") as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = sample_response
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            papers = await scraper.fetch_recent_papers(days=7)

            assert len(papers) == 2
            assert papers[0].title == "Test Paper 1"
            assert papers[0].source == "papers_with_code"
            assert papers[0].id.startswith("pwc_")
            assert len(papers[0].authors) == 2

    @pytest.mark.asyncio
    async def test_fetch_empty_results(self, scraper: PapersWithCodeScraper) -> None:
        """Test Papers with Code fetch with no results."""
        empty_response = {"count": 0, "next": None, "previous": None, "results": []}

        with patch("httpx.AsyncClient.get") as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = empty_response
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            papers = await scraper.fetch_recent_papers(days=7)

            assert len(papers) == 0

    @pytest.mark.asyncio
    async def test_fetch_network_error(self, scraper: PapersWithCodeScraper) -> None:
        """Test Papers with Code fetch handling network errors."""
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_get.side_effect = httpx.RequestError("Network error")

            papers = await scraper.fetch_recent_papers(days=7)

            assert papers == []

    @pytest.mark.asyncio
    async def test_date_filtering(self, scraper: PapersWithCodeScraper) -> None:
        """Test that old papers are filtered out correctly."""
        sample_papers = [
            {
                "id": "paper-recent",
                "title": "Recent Paper",
                "abstract": "Recent abstract",
                "published": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
                "authors": [{"name": "Recent Author"}],
                "url_abs": "https://arxiv.org/abs/2411.12345",
            },
            {
                "id": "paper-old",
                "title": "Old Paper",
                "abstract": "Old abstract",
                "published": "2020-01-01T00:00:00Z",
                "authors": [{"name": "Old Author"}],
                "url_abs": "https://arxiv.org/abs/2001.12345",
            },
        ]

        async def mock_fetch_page(page, items_per_page, cutoff_date):
            return scraper._parse_papers_response({"results": sample_papers}, cutoff_date)

        with patch.object(scraper, "_fetch_page", side_effect=mock_fetch_page):
            papers = await scraper.fetch_recent_papers(days=7)

            assert len(papers) == 1
            assert papers[0].title == "Recent Paper"

    @pytest.mark.asyncio
    async def test_skip_papers_without_abstract(self, scraper: PapersWithCodeScraper) -> None:
        """Test that papers without abstracts are skipped."""
        sample_papers = [
            {
                "id": "paper-with-abstract",
                "title": "Good Paper",
                "abstract": "This has an abstract",
                "published": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
                "authors": [{"name": "Author"}],
                "url_abs": "https://arxiv.org/abs/2411.12345",
            },
            {
                "id": "paper-no-abstract",
                "title": "Bad Paper",
                "abstract": "",
                "published": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
                "authors": [{"name": "Author"}],
                "url_abs": "https://arxiv.org/abs/2411.54321",
            },
        ]

        async def mock_fetch_page(page, items_per_page, cutoff_date):
            return scraper._parse_papers_response({"results": sample_papers}, cutoff_date)

        with patch.object(scraper, "_fetch_page", side_effect=mock_fetch_page):
            papers = await scraper.fetch_recent_papers(days=7)

            assert len(papers) == 1
            assert papers[0].abstract != ""

    @pytest.mark.asyncio
    async def test_fallback_url_generation(self, scraper: PapersWithCodeScraper) -> None:
        """Test URL generation when url_abs is missing."""
        sample_papers = [
            {
                "id": "paper-no-url",
                "title": "Paper Without URL",
                "abstract": "Test abstract",
                "published": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
                "authors": [{"name": "Author"}],
                "url_abs": "",
                "arxiv_id": "",
            }
        ]

        async def mock_fetch_page(page, items_per_page, cutoff_date):
            return scraper._parse_papers_response({"results": sample_papers}, cutoff_date)

        with patch.object(scraper, "_fetch_page", side_effect=mock_fetch_page):
            papers = await scraper.fetch_recent_papers(days=7)

            assert len(papers) == 1
            assert papers[0].url == "https://paperswithcode.com/paper/paper-no-url"

    @pytest.mark.asyncio
    async def test_html_response_error(self, scraper: PapersWithCodeScraper) -> None:
        """Test proper error handling when API returns HTML instead of JSON."""
        mock_response = Mock()
        mock_response.headers = {"content-type": "text/html"}
        mock_response.text = "<html><body>Login required</body></html>"
        mock_response.raise_for_status = Mock()

        mock_client_instance = Mock()
        mock_client_instance.get = AsyncMock(return_value=mock_response)

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value = mock_client_instance

            with pytest.raises(ValueError, match="API returned text/html instead of JSON"):
                await scraper._fetch_from_api("https://test.com")

    @pytest.mark.asyncio
    async def test_invalid_json_response_error(self, scraper: PapersWithCodeScraper) -> None:
        """Test proper error handling when API returns invalid JSON."""
        mock_response = Mock()
        mock_response.headers = {"content-type": "application/json"}
        mock_response.text = "not valid json"
        mock_response.json.side_effect = JSONDecodeError("Expecting value", "doc", 0)
        mock_response.raise_for_status = Mock()

        mock_client_instance = Mock()
        mock_client_instance.get = AsyncMock(return_value=mock_response)

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value = mock_client_instance

            with pytest.raises(ValueError, match="Invalid JSON response from API"):
                await scraper._fetch_from_api("https://test.com")

    @pytest.mark.asyncio
    async def test_api_key_usage(self, scraper: PapersWithCodeScraper) -> None:
        """Test that API key is used when available."""
        mock_response = Mock()
        mock_response.headers = {"content-type": "application/json"}
        mock_response.json.return_value = {"results": []}
        mock_response.raise_for_status = Mock()

        mock_client_instance = Mock()
        mock_get = AsyncMock(return_value=mock_response)
        mock_client_instance.get = mock_get

        with (
            patch("httpx.AsyncClient") as mock_client,
            patch.dict(os.environ, {"PAPERS_WITH_CODE_API_KEY": "test-key-123"}),
        ):
            mock_client.return_value.__aenter__.return_value = mock_client_instance

            await scraper._fetch_from_api("https://test.com")

            mock_get.assert_called_once()
            call_kwargs = mock_get.call_args.kwargs
            assert "headers" in call_kwargs
            assert call_kwargs["headers"]["Authorization"] == "Token test-key-123"

    @pytest.mark.asyncio
    async def test_no_api_key(self, scraper: PapersWithCodeScraper) -> None:
        """Test that request works without API key (may be rate-limited)."""
        mock_response = Mock()
        mock_response.headers = {"content-type": "application/json"}
        mock_response.json.return_value = {"results": []}
        mock_response.raise_for_status = Mock()

        mock_client_instance = Mock()
        mock_get = AsyncMock(return_value=mock_response)
        mock_client_instance.get = mock_get

        with patch("httpx.AsyncClient") as mock_client, patch.dict(os.environ, {}, clear=True):
            mock_client.return_value.__aenter__.return_value = mock_client_instance

            await scraper._fetch_from_api("https://test.com")

            mock_get.assert_called_once()
            call_kwargs = mock_get.call_args.kwargs
            assert "headers" in call_kwargs
            assert call_kwargs["headers"] == {}
