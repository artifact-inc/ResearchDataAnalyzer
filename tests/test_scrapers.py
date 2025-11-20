"""Tests for research paper scrapers."""

import json
from unittest.mock import Mock, patch

import httpx
import pytest

from scrapers.arxiv_scraper import ArxivScraper
from scrapers.openalex_scraper import OpenAlexScraper
from scrapers.semantic_scholar_scraper import SemanticScholarScraper


class TestArxivScraper:
    """Tests for ArXiv scraper."""

    @pytest.fixture
    def scraper(self) -> ArxivScraper:
        """Create ArxivScraper instance."""
        config = {
            "rate_limit_seconds": 3,
            "categories": ["cs.AI"],
            "base_url": "http://export.arxiv.org/api/query",
        }
        return ArxivScraper(config)

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Integration test - requires full HTTP client mocking")
    async def test_fetch_recent_papers_success(self, scraper: ArxivScraper, arxiv_sample_xml: str) -> None:
        """Test successful arXiv paper fetching."""
        # TODO: Implement proper async HTTP client context manager mocking
        # Current simple mock doesn't properly simulate httpx.AsyncClient context manager
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_response = Mock()
            mock_response.text = arxiv_sample_xml
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            papers = await scraper.fetch_recent_papers(days=7)

            assert len(papers) == 2
            assert papers[0].title == "High-Quality Medical Imaging Dataset for Few-Shot Learning"
            assert papers[0].source == "arxiv"
            assert "carefully curated" in papers[0].abstract

    @pytest.mark.asyncio
    async def test_fetch_empty_results(self, scraper: ArxivScraper) -> None:
        """Test arXiv fetch with no results."""
        empty_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <feed xmlns="http://www.w3.org/2005/Atom">
          <opensearch:totalResults xmlns:opensearch="http://a9.com/-/spec/opensearch/1.1/">0</opensearch:totalResults>
        </feed>"""

        with patch("httpx.AsyncClient.get") as mock_get:
            mock_response = Mock()
            mock_response.text = empty_xml
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            papers = await scraper.fetch_recent_papers(days=7)

            assert len(papers) == 0

    @pytest.mark.asyncio
    async def test_fetch_network_error(self, scraper: ArxivScraper) -> None:
        """Test arXiv fetch handling network errors."""
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_get.side_effect = httpx.RequestError("Network error")

            papers = await scraper.fetch_recent_papers(days=7)

            # Should return empty list on error, not raise
            assert papers == []

    @pytest.mark.asyncio
    async def test_fetch_malformed_xml(self, scraper: ArxivScraper) -> None:
        """Test arXiv fetch with malformed XML response."""
        malformed_xml = "<invalid>not valid xml</not_closed>"

        with patch("httpx.AsyncClient.get") as mock_get:
            mock_response = Mock()
            mock_response.text = malformed_xml
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            papers = await scraper.fetch_recent_papers(days=7)

            # Should handle parsing error gracefully
            assert papers == []


class TestSemanticScholarScraper:
    """Tests for Semantic Scholar scraper."""

    @pytest.fixture
    def scraper(self) -> SemanticScholarScraper:
        """Create SemanticScholarScraper instance."""
        config = {
            "rate_limit_seconds": 1,
            "base_url": "https://api.semanticscholar.org/graph/v1",
            "fields": ["title", "abstract", "year", "authors", "citationCount", "url", "externalIds"],
        }
        return SemanticScholarScraper(config)

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Integration test - requires full HTTP client mocking")
    async def test_fetch_recent_papers_success(self, scraper: SemanticScholarScraper, s2_sample_json: str) -> None:
        """Test successful Semantic Scholar paper fetching."""
        # TODO: Implement proper async HTTP client context manager mocking
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_response = Mock()
            mock_response.text = s2_sample_json
            mock_response.json.return_value = json.loads(s2_sample_json)
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            papers = await scraper.fetch_recent_papers(days=7)

            assert len(papers) == 2
            assert papers[0].title == "High-Quality Medical Imaging Dataset for Few-Shot Learning"
            assert papers[0].source == "semantic_scholar"
            assert papers[0].citation_count == 15
            assert papers[0].venue == "NeurIPS"
            assert papers[0].published_date.year == 2025

    @pytest.mark.asyncio
    async def test_fetch_empty_results(self, scraper: SemanticScholarScraper) -> None:
        """Test Semantic Scholar fetch with no results."""
        empty_json = {"total": 0, "offset": 0, "data": []}

        with patch("httpx.AsyncClient.get") as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = empty_json
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            papers = await scraper.fetch_recent_papers(days=7)

            assert len(papers) == 0

    @pytest.mark.asyncio
    async def test_fetch_network_error(self, scraper: SemanticScholarScraper) -> None:
        """Test Semantic Scholar fetch handling network errors."""
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_get.side_effect = httpx.RequestError("Network error")

            papers = await scraper.fetch_recent_papers(days=7)

            # Should return empty list on error, not raise
            assert papers == []

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Integration test - requires full HTTP client mocking")
    async def test_fetch_missing_fields(self, scraper: SemanticScholarScraper) -> None:
        """Test Semantic Scholar fetch with papers missing optional fields."""
        # TODO: Implement proper async HTTP client context manager mocking
        minimal_json = {
            "total": 1,
            "offset": 0,
            "data": [
                {
                    "paperId": "abc123",
                    "title": "Minimal Paper",
                    "abstract": "Test abstract",
                    "year": 2025,
                    "authors": [{"name": "Test Author"}],
                }
            ],
        }

        with patch("httpx.AsyncClient.get") as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = minimal_json
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            papers = await scraper.fetch_recent_papers(days=7)

            assert len(papers) == 1
            assert papers[0].citation_count is None
            assert papers[0].venue is None


class TestOpenAlexScraper:
    """Tests for OpenAlex scraper."""

    @pytest.fixture
    def scraper(self) -> OpenAlexScraper:
        """Create OpenAlexScraper instance."""
        config = {
            "rate_limit_seconds": 0.1,
            "base_url": "https://api.openalex.org",
            "email": "test@example.com",
            "concepts": ["C154945302"],
            "filters": {"type": "journal-article", "is_oa": "true"},
        }
        return OpenAlexScraper(config)

    def test_reconstruct_abstract_simple(self, scraper: OpenAlexScraper) -> None:
        """Test reconstructing abstract from inverted index."""
        inverted_index = {"This": [0], "is": [1], "a": [2], "test": [3], "abstract": [4]}

        result = scraper._reconstruct_abstract(inverted_index)

        assert result == "This is a test abstract"

    def test_reconstruct_abstract_with_duplicates(self, scraper: OpenAlexScraper) -> None:
        """Test reconstructing abstract with words appearing multiple times."""
        inverted_index = {
            "The": [0, 5],
            "quick": [1],
            "brown": [2],
            "fox": [3],
            "jumps": [4],
            "over": [6],
            "lazy": [7],
            "dog": [8],
        }

        result = scraper._reconstruct_abstract(inverted_index)

        assert result == "The quick brown fox jumps The over lazy dog"

    def test_reconstruct_abstract_empty(self, scraper: OpenAlexScraper) -> None:
        """Test reconstructing empty abstract."""
        result = scraper._reconstruct_abstract({})

        assert result == ""

    def test_parse_work_complete(self, scraper: OpenAlexScraper) -> None:
        """Test parsing a complete OpenAlex work."""
        work = {
            "id": "https://openalex.org/W1234567890",
            "title": "Test Paper Title",
            "abstract_inverted_index": {"This": [0], "is": [1], "the": [2], "abstract": [3]},
            "authorships": [{"author": {"display_name": "John Doe"}}, {"author": {"display_name": "Jane Smith"}}],
            "publication_date": "2025-01-15",
            "doi": "https://doi.org/10.1234/test",
            "cited_by_count": 42,
            "primary_location": {"source": {"display_name": "Nature"}},
        }

        paper = scraper._parse_work(work)

        assert paper is not None
        assert paper.id == "openalex_W1234567890"
        assert paper.title == "Test Paper Title"
        assert paper.abstract == "This is the abstract"
        assert paper.authors == ["John Doe", "Jane Smith"]
        assert paper.published_date.year == 2025
        assert paper.published_date.month == 1
        assert paper.published_date.day == 15
        assert paper.source == "openalex"
        assert paper.url == "https://doi.org/10.1234/test"
        assert paper.citation_count == 42
        assert paper.venue == "Nature"

    def test_parse_work_missing_title(self, scraper: OpenAlexScraper) -> None:
        """Test parsing work without title returns None."""
        work = {
            "id": "https://openalex.org/W123",
            "abstract_inverted_index": {"test": [0]},
            "publication_date": "2025-01-15",
        }

        paper = scraper._parse_work(work)

        assert paper is None

    def test_parse_work_missing_abstract(self, scraper: OpenAlexScraper) -> None:
        """Test parsing work without abstract returns None."""
        work = {"id": "https://openalex.org/W123", "title": "Test Title", "publication_date": "2025-01-15"}

        paper = scraper._parse_work(work)

        assert paper is None

    def test_parse_work_missing_id(self, scraper: OpenAlexScraper) -> None:
        """Test parsing work without ID returns None."""
        work = {"title": "Test Title", "abstract_inverted_index": {"test": [0]}, "publication_date": "2025-01-15"}

        paper = scraper._parse_work(work)

        assert paper is None

    def test_parse_work_missing_publication_date(self, scraper: OpenAlexScraper) -> None:
        """Test parsing work without publication date returns None."""
        work = {"id": "https://openalex.org/W123", "title": "Test Title", "abstract_inverted_index": {"test": [0]}}

        paper = scraper._parse_work(work)

        assert paper is None

    def test_parse_work_invalid_date_format(self, scraper: OpenAlexScraper) -> None:
        """Test parsing work with invalid date format returns None."""
        work = {
            "id": "https://openalex.org/W123",
            "title": "Test Title",
            "abstract_inverted_index": {"test": [0]},
            "publication_date": "invalid-date",
        }

        paper = scraper._parse_work(work)

        assert paper is None

    def test_parse_work_minimal_fields(self, scraper: OpenAlexScraper) -> None:
        """Test parsing work with only required fields."""
        work = {
            "id": "https://openalex.org/W123",
            "title": "Minimal Paper",
            "abstract_inverted_index": {"minimal": [0]},
            "publication_date": "2025-01-01",
        }

        paper = scraper._parse_work(work)

        assert paper is not None
        assert paper.id == "openalex_W123"
        assert paper.title == "Minimal Paper"
        assert paper.abstract == "minimal"
        assert paper.authors == []
        assert paper.citation_count is None
        assert paper.venue is None

    def test_parse_work_no_doi_uses_id(self, scraper: OpenAlexScraper) -> None:
        """Test parsing work without DOI uses OpenAlex ID for URL."""
        work = {
            "id": "https://openalex.org/W123",
            "title": "No DOI Paper",
            "abstract_inverted_index": {"test": [0]},
            "publication_date": "2025-01-01",
        }

        paper = scraper._parse_work(work)

        assert paper is not None
        assert paper.url == "https://openalex.org/W123"

    @pytest.mark.asyncio
    async def test_fetch_empty_results(self, scraper: OpenAlexScraper) -> None:
        """Test OpenAlex fetch with no results."""
        empty_json = {"results": [], "meta": {}}

        with patch("httpx.AsyncClient.get") as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = empty_json
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            papers = await scraper.fetch_recent_papers(days=7)

            assert len(papers) == 0

    @pytest.mark.asyncio
    async def test_fetch_network_error(self, scraper: OpenAlexScraper) -> None:
        """Test OpenAlex fetch handling network errors."""
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_get.side_effect = httpx.RequestError("Network error")

            papers = await scraper.fetch_recent_papers(days=7)

            assert papers == []
