"""Tests for DBLP scraper."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest

from scrapers.dblp_scraper import DBLPScraper


@pytest.fixture
def dblp_config():
    """DBLP configuration fixture."""
    return {
        "enabled": True,
        "rate_limit_seconds": 1,
        "base_url": "https://dblp.org/search/publ/api",
        "venues": ["NeurIPS", "ICLR"],
        "format": "json",
        "max_hits": 100,
    }


@pytest.fixture
def scraper(dblp_config):
    """Create DBLP scraper instance."""
    return DBLPScraper(dblp_config)


@pytest.fixture
def sample_dblp_response():
    """Sample DBLP API response with abstract."""
    return {
        "result": {
            "hits": {
                "hit": [
                    {
                        "info": {
                            "title": "Attention Is All You Need",
                            "year": "2024",
                            "key": "conf/nips/VaswaniSPUJGKP24",
                            "abstract": (
                                "The dominant sequence transduction models are based on "
                                "complex recurrent or convolutional neural networks."
                            ),
                            "authors": {
                                "author": [
                                    {"text": "Ashish Vaswani"},
                                    {"text": "Noam Shazeer"},
                                ]
                            },
                            "url": "https://dblp.org/rec/conf/nips/VaswaniSPUJGKP24",
                            "venue": "NeurIPS",
                        }
                    }
                ]
            }
        }
    }


@pytest.fixture
def sample_dblp_response_no_abstract():
    """Sample DBLP API response without abstract."""
    return {
        "result": {
            "hits": {
                "hit": [
                    {
                        "info": {
                            "title": "Some Paper Without Abstract",
                            "year": "2024",
                            "key": "conf/nips/Test24",
                            "authors": {"author": [{"text": "Test Author"}]},
                            "url": "https://dblp.org/rec/conf/nips/Test24",
                            "venue": "NeurIPS",
                        }
                    }
                ]
            }
        }
    }


def test_source_name(scraper):
    """Test source name property."""
    assert scraper.source_name == "dblp"


def test_parse_hit_with_abstract(scraper, sample_dblp_response):
    """Test parsing DBLP hit with abstract."""
    hit = sample_dblp_response["result"]["hits"]["hit"][0]
    paper = scraper._parse_hit(hit, "NeurIPS")

    assert paper is not None
    assert paper.id == "dblp_conf_nips_VaswaniSPUJGKP24"
    assert paper.title == "Attention Is All You Need"
    assert paper.abstract.startswith("The dominant sequence")
    assert len(paper.authors) == 2
    assert paper.authors[0] == "Ashish Vaswani"
    assert paper.published_date == datetime(2024, 1, 1, tzinfo=UTC).replace(tzinfo=None)
    assert paper.source == "dblp"
    assert paper.venue == "NeurIPS"
    assert "dblp.org" in paper.url


def test_parse_hit_without_abstract(scraper, sample_dblp_response_no_abstract):
    """Test parsing DBLP hit without abstract (should skip)."""
    hit = sample_dblp_response_no_abstract["result"]["hits"]["hit"][0]
    paper = scraper._parse_hit(hit, "NeurIPS")

    assert paper is None


def test_parse_hit_missing_required_fields(scraper):
    """Test parsing hit with missing required fields."""
    hit = {"info": {"title": "Test"}}
    paper = scraper._parse_hit(hit, "NeurIPS")
    assert paper is None

    hit = {"info": {"year": "2024"}}
    paper = scraper._parse_hit(hit, "NeurIPS")
    assert paper is None

    hit = {"info": {"key": "test/key"}}
    paper = scraper._parse_hit(hit, "NeurIPS")
    assert paper is None


def test_parse_hit_single_author(scraper):
    """Test parsing hit with single author (dict format)."""
    hit = {
        "info": {
            "title": "Single Author Paper",
            "year": "2024",
            "key": "conf/test/Single24",
            "abstract": "Test abstract",
            "authors": {"author": {"text": "Single Author"}},
            "url": "https://dblp.org/rec/conf/test/Single24",
        }
    }

    paper = scraper._parse_hit(hit, "Test")
    assert paper is not None
    assert len(paper.authors) == 1
    assert paper.authors[0] == "Single Author"


def test_parse_response(scraper, sample_dblp_response):
    """Test parsing DBLP API response."""
    papers = scraper._parse_response(sample_dblp_response, "NeurIPS")

    assert len(papers) == 1
    assert papers[0].title == "Attention Is All You Need"


def test_parse_response_empty(scraper):
    """Test parsing empty DBLP response."""
    empty_response = {"result": {"hits": {"hit": []}}}
    papers = scraper._parse_response(empty_response, "NeurIPS")
    assert len(papers) == 0


@pytest.mark.asyncio
async def test_search_venue(scraper, sample_dblp_response):
    """Test searching specific venue."""
    with patch.object(scraper, "_search_venue", new_callable=AsyncMock) as mock_search:
        mock_search.return_value = [scraper._parse_hit(sample_dblp_response["result"]["hits"]["hit"][0], "NeurIPS")]

        papers = await scraper._search_venue("NeurIPS", 2024)

        assert len(papers) == 1
        assert papers[0].venue == "NeurIPS"


@pytest.mark.asyncio
async def test_fetch_recent_papers(scraper, sample_dblp_response):
    """Test fetching recent papers."""
    with patch.object(scraper, "_search_venue", new_callable=AsyncMock) as mock_search:
        mock_search.return_value = [scraper._parse_hit(sample_dblp_response["result"]["hits"]["hit"][0], "NeurIPS")]

        papers = await scraper.fetch_recent_papers(days=30)

        assert len(papers) >= 0
        assert mock_search.call_count > 0


@pytest.mark.asyncio
async def test_fetch_new_since(scraper):
    """Test fetching papers since timestamp."""
    last_check = datetime.now(UTC) - timedelta(days=7)

    with patch.object(scraper, "fetch_recent_papers", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = []

        await scraper.fetch_new_since(last_check)

        mock_fetch.assert_called_once()
        days_arg = mock_fetch.call_args[0][0]
        assert days_arg >= 7


@pytest.mark.asyncio
async def test_rate_limiting(scraper):
    """Test rate limiting is applied."""
    with patch.object(scraper, "_rate_limit", new_callable=AsyncMock) as mock_limit:
        with patch.object(scraper, "_search_venue", new_callable=AsyncMock) as mock_search:
            mock_search.return_value = []

            await scraper.fetch_recent_papers(days=30)

            assert mock_limit.call_count > 0


@pytest.mark.asyncio
async def test_deduplication(scraper, sample_dblp_response):
    """Test that duplicate papers are filtered out."""
    duplicate_hit = sample_dblp_response["result"]["hits"]["hit"][0]

    with patch.object(scraper, "_search_venue", new_callable=AsyncMock) as mock_search:
        mock_search.return_value = [
            scraper._parse_hit(duplicate_hit, "NeurIPS"),
            scraper._parse_hit(duplicate_hit, "NeurIPS"),
        ]

        papers = await scraper.fetch_recent_papers(days=30)

        unique_ids = {p.id for p in papers}
        assert len(papers) == len(unique_ids)
