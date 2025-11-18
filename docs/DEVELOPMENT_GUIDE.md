# Development Guide

Guide for developing, testing, and extending the Research Data Analyzer.

---

## Table of Contents

1. [Setup for Development](#setup-for-development)
2. [Project Structure](#project-structure)
3. [Development Workflow](#development-workflow)
4. [Testing Guidelines](#testing-guidelines)
5. [Adding New Features](#adding-new-features)
6. [Code Style and Standards](#code-style-and-standards)
7. [Debugging](#debugging)
8. [Performance Optimization](#performance-optimization)

---

## Setup for Development

### Prerequisites

- **Python 3.11+** (required)
- **uv** (package manager)
- **Git**
- **Anthropic API key** (for AI evaluation)

### Initial Setup

```bash
# Clone repository
cd ai_working/research_data_analyzer

# Create virtual environment and install dependencies
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install with uv (from project directory)
uv sync

# Or install manually
pip install anthropic httpx python-dotenv pytest pytest-asyncio

# Setup environment
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

### Environment Variables

**Required:**
- `ANTHROPIC_API_KEY` - Your Anthropic API key

**Optional:**
- `SEMANTIC_SCHOLAR_API_KEY` - For higher rate limits
- `LOG_LEVEL` - Logging level (DEBUG, INFO, WARNING, ERROR)

### Verify Installation

```bash
# Run tests
pytest

# Run type checking
pyright

# Run linting
ruff check .

# Run formatting check
ruff format --check .
```

---

## Project Structure

```
research_data_analyzer/
├── models/                  # Data structures
│   ├── paper.py            # Paper dataclass
│   └── opportunity.py      # OpportunityAssessment, Blocker, UncertaintySource
│
├── config/                  # Configuration loaders
│   └── __init__.py         # Load heuristics, sources, thresholds
│
├── scrapers/                # Paper sources
│   ├── base.py             # BaseScraper abstract class
│   ├── arxiv.py            # arXiv scraper
│   └── semantic_scholar.py # Semantic Scholar scraper
│
├── analyzers/               # Signal extraction & AI evaluation
│   ├── signal_extractor.py      # Heuristic signal detection
│   ├── value_evaluator.py       # Claude-based evaluation
│   ├── quality_filter.py        # Pre-filter papers
│   ├── blocker_detector.py      # Blocker detection
│   ├── confidence_calculator.py # Confidence scoring
│   └── opportunity_scorer.py    # Scoring utilities
│
├── monitor/                 # Processing modes
│   ├── batch_processor.py  # One-time batch analysis
│   └── continuous_monitor.py # Continuous monitoring
│
├── persistence/             # Output handling
│   └── output_writer.py    # Write findings to files
│
├── tests/                   # Test suite
│   ├── conftest.py         # Pytest fixtures
│   ├── fixtures/           # Test data
│   ├── test_models.py
│   ├── test_signal_extractor.py
│   ├── test_value_evaluator.py
│   └── test_scrapers.py
│
├── main.py                  # CLI entry point
└── config/                  # Configuration files
    ├── heuristics.json
    └── sources.json
```

### Import Conventions

**Use relative imports within the package:**

```python
# Good
from models.paper import Paper
from analyzers.signal_extractor import SignalExtractor

# Bad
from research_data_analyzer.models.paper import Paper
```

**Running as module:**

```bash
# From project root (ai_working/research_data_analyzer)
python -m main --mode batch
```

---

## Development Workflow

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Changes

Follow the [Code Style](#code-style-and-standards) guidelines.

### 3. Write Tests

All new features must have tests (see [Testing Guidelines](#testing-guidelines)).

### 4. Run Quality Checks

```bash
# Format code
ruff format .

# Fix linting issues
ruff check --fix .

# Type check
pyright

# Run tests
pytest -v
```

### 5. Commit Changes

Follow conventional commit format:

```bash
git commit -m "feat: add new signal category for domain expertise"
git commit -m "fix: handle missing citation_count in papers"
git commit -m "docs: update API reference for BlockerDetector"
```

### 6. Submit PR

Push branch and create pull request with:
- Clear description of changes
- Test results
- Any breaking changes noted

---

## Testing Guidelines

### Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_signal_extractor.py

# Run specific test
pytest tests/test_signal_extractor.py::test_extract_demand_signals

# Run with coverage
pytest --cov=. --cov-report=html
```

### Test Structure

**Use pytest fixtures for common setup:**

```python
# tests/conftest.py
import pytest
from models.paper import Paper
from datetime import datetime, UTC

@pytest.fixture
def sample_paper():
    return Paper(
        id="test:001",
        title="Test Paper",
        abstract="This is a test abstract with limited data and scarcity issues.",
        authors=["Test Author"],
        published_date=datetime.now(UTC),
        source="test",
        url="https://example.com/paper",
        citation_count=10
    )
```

**Write focused unit tests:**

```python
# tests/test_signal_extractor.py
def test_extract_scarcity_signals(sample_paper):
    """Test scarcity signal detection."""
    extractor = SignalExtractor(config)
    signals = extractor.extract(sample_paper)

    assert signals["scarcity"]["score"] > 0
    assert "scarcity_complaint" in signals["demand"]["detected"]
```

### Test Coverage Requirements

- **Minimum 80% coverage** for new code
- **100% coverage** for critical paths:
  - Signal extraction logic
  - Blocker detection
  - Score calculation
  - Tier assignment

### Integration Tests

**Test complete workflows:**

```python
@pytest.mark.asyncio
async def test_complete_analysis_pipeline(sample_paper):
    """Test end-to-end analysis."""
    extractor = SignalExtractor(config)
    evaluator = ValueEvaluator(config)
    writer = OutputWriter(tmp_path)

    # Extract signals
    signals = extractor.extract(sample_paper)

    # Evaluate
    assessment = await evaluator.evaluate(sample_paper, signals, config)

    # Write
    filepath = writer.write_finding(assessment)

    assert filepath.exists()
    assert assessment.tier in ["S", "A", "B", "C", "D"]
```

### Async Testing

Use `pytest-asyncio` for async tests:

```python
import pytest

@pytest.mark.asyncio
async def test_scraper_fetch():
    scraper = ArxivScraper(config)
    papers = await scraper.fetch_recent_papers(days=1)
    assert len(papers) >= 0
```

### Mock External APIs

**Mock API calls in tests:**

```python
from unittest.mock import patch, AsyncMock

@pytest.mark.asyncio
@patch('anthropic.Anthropic')
async def test_value_evaluator_mock(mock_anthropic, sample_paper):
    """Test evaluator with mocked Claude API."""
    mock_client = mock_anthropic.return_value
    mock_client.messages.create = AsyncMock(return_value=mock_response)

    evaluator = ValueEvaluator(config)
    assessment = await evaluator.evaluate(sample_paper, signals, config)

    assert assessment is not None
```

---

## Adding New Features

### Adding a New Signal Category

**1. Update heuristics config (`config/heuristics.json`):**

```json
{
  "keywords": {
    "domain_expertise": [
      "domain expert",
      "specialist knowledge",
      "expert curation"
    ]
  }
}
```

**2. Add detection method (`analyzers/signal_extractor.py`):**

```python
def _extract_domain_expertise_signals(self, text: str) -> dict:
    """Extract domain expertise signals."""
    score = 0.0
    detected = []

    expertise_keywords = self.keywords.get("domain_expertise", [])
    matches = sum(1 for kw in expertise_keywords if kw.lower() in text)

    if matches > 0:
        score += min(matches * 3.0, 9.0)
        detected.append("domain_expertise_mentioned")

    return {"score": min(score, 10.0), "detected": detected}
```

**3. Add to extract method:**

```python
def extract(self, paper: Paper) -> dict[str, dict]:
    text = f"{paper.title} {paper.abstract}".lower()

    signals = {
        # ... existing signals
        "domain_expertise": self._extract_domain_expertise_signals(text),
    }

    return signals
```

**4. Write tests:**

```python
def test_extract_domain_expertise_signals():
    config = {"keywords": {"domain_expertise": ["domain expert"]}}
    extractor = SignalExtractor(config)

    paper = Paper(
        id="test:001",
        title="Domain Expert Curation",
        abstract="Dataset curated by domain experts...",
        # ... other fields
    )

    signals = extractor.extract(paper)
    assert signals["domain_expertise"]["score"] > 0
```

---

### Creating a New Scraper

**1. Create scraper file (`scrapers/my_source.py`):**

```python
from datetime import datetime
from scrapers.base import BaseScraper
from models.paper import Paper
import httpx

class MySourceScraper(BaseScraper):
    @property
    def source_name(self) -> str:
        return "My Source"

    async def fetch_recent_papers(self, days: int) -> list[Paper]:
        """Fetch papers from last N days."""
        await self._rate_limit()

        async with httpx.AsyncClient() as client:
            # Wrap in retry logic for rate limits
            papers = await self._retry_with_backoff(
                lambda: self._fetch_with_client(client, days)
            )

        return papers

    async def _fetch_with_client(self, client: httpx.AsyncClient, days: int) -> list[Paper]:
        """Implementation with client."""
        url = f"https://api.mysource.com/papers?days={days}"
        response = await client.get(url)
        response.raise_for_status()

        data = response.json()
        return [self._parse_paper(item) for item in data["results"]]

    def _parse_paper(self, item: dict) -> Paper:
        """Parse API response into Paper object."""
        return Paper(
            id=item["id"],
            title=item["title"],
            abstract=item["abstract"],
            authors=item["authors"],
            published_date=datetime.fromisoformat(item["published"]),
            source=self.source_name,
            url=item["url"],
            citation_count=item.get("citations"),
            venue=item.get("venue")
        )

    async def fetch_new_since(self, last_check: datetime) -> list[Paper]:
        """Fetch papers since timestamp."""
        # Similar to fetch_recent_papers but with timestamp filter
        pass
```

**2. Add configuration (`config/sources.json`):**

```json
{
  "my_source": {
    "enabled": true,
    "rate_limit_seconds": 1
  }
}
```

**3. Register scraper (`scrapers/__init__.py`):**

```python
from .my_source import MySourceScraper

def create_scrapers(sources_config: dict) -> list:
    scrapers = []

    if sources_config.get("my_source", {}).get("enabled"):
        scrapers.append(MySourceScraper(sources_config["my_source"]))

    # ... other scrapers

    return scrapers
```

**4. Write tests:**

```python
@pytest.mark.asyncio
async def test_my_source_scraper():
    config = {"rate_limit_seconds": 0.1}
    scraper = MySourceScraper(config)

    papers = await scraper.fetch_recent_papers(days=7)

    assert len(papers) > 0
    assert all(isinstance(p, Paper) for p in papers)
    assert scraper.source_name == "My Source"
```

---

### Modifying AI Prompts

**Location:** `analyzers/value_evaluator.py` → `_create_evaluation_prompt()`

**Guidelines:**
1. **Be specific:** Request concrete examples and evidence
2. **Avoid generics:** Flag vague language like "high demand"
3. **Structure output:** Always request JSON format
4. **Separate concerns:** Use dual scoring (technical vs commercial)
5. **Document changes:** Note prompt versions in comments

**Testing prompt changes:**

```python
# Create test with known good/bad papers
@pytest.mark.asyncio
async def test_prompt_rejects_generic_language():
    """Ensure prompt flags generic business language."""
    paper = create_paper_with_generic_abstract()

    evaluator = ValueEvaluator(config)
    assessment = await evaluator.evaluate(paper, signals, config)

    # Should have uncertainty flagged or low commercial score
    assert (
        assessment.commercial_viability_score < 6.0 or
        len(assessment.uncertainty_sources) > 0
    )
```

---

### Extending Quality Filters

**Add new filter criteria (`analyzers/quality_filter.py`):**

```python
@dataclass
class FilterConfig:
    min_abstract_length: int = 100
    min_author_count: int = 1
    max_age_days: int = 365
    require_venue: bool = False
    min_citations: int = 0
    require_dataset_mention: bool = False  # NEW

def _passes_filters(paper: Paper, config: FilterConfig) -> tuple[bool, str | None]:
    """Check if paper passes quality filters."""

    # ... existing checks

    # NEW: Check for dataset mentions
    if config.require_dataset_mention:
        if not paper.dataset_mentions:
            return False, "No dataset mentions found"

    return True, None
```

---

## Code Style and Standards

### Python Style

**Follow PEP 8 with these specifics:**

```python
# Line length: 120 characters
# Use ruff for formatting

# Type hints: Required for all functions
def process_paper(paper: Paper, config: dict) -> OpportunityAssessment | None:
    """Process a single paper."""
    pass

# Docstrings: Use Google style
def extract_signals(text: str) -> dict[str, float]:
    """Extract signals from text.

    Args:
        text: Input text to analyze

    Returns:
        Dictionary mapping signal names to scores (0-10)

    Raises:
        ValueError: If text is empty
    """
    pass
```

### Formatting

**Use ruff for formatting:**

```bash
# Format all files
ruff format .

# Check formatting without changing
ruff format --check .
```

### Linting

**Use ruff for linting:**

```bash
# Check all issues
ruff check .

# Auto-fix issues
ruff check --fix .
```

### Type Checking

**Use pyright:**

```bash
# Check all files
pyright

# Check specific file
pyright analyzers/signal_extractor.py
```

**Handle dynamic types:**

```python
# For Anthropic API response (dynamic content blocks)
for block in response.content:
    if hasattr(block, "text"):
        result_text = block.text  # type: ignore[attr-defined]
```

### Import Organization

**Order:**
1. Standard library
2. Third-party packages
3. Local modules

```python
import json
import logging
from datetime import datetime, UTC

import httpx
from anthropic import Anthropic

from models.paper import Paper
from analyzers.signal_extractor import SignalExtractor
```

### Naming Conventions

- **Classes:** PascalCase (`SignalExtractor`)
- **Functions/methods:** snake_case (`extract_signals`)
- **Constants:** UPPER_SNAKE_CASE (`BLOCKER_PATTERNS`)
- **Private methods:** Prefix with `_` (`_rate_limit`)

---

## Debugging

### Logging

**Use structured logging:**

```python
import logging

logger = logging.getLogger(__name__)

# In code
logger.debug(f"Processing paper: {paper.id}")
logger.info(f"Found {len(papers)} papers")
logger.warning(f"Rate limit approaching: {remaining_calls}")
logger.error(f"Failed to parse response: {error}")
```

**Configure log level:**

```bash
# In .env
LOG_LEVEL=DEBUG

# Or command line
python -m main --log-level DEBUG --mode batch
```

**View logs:**

```bash
# Real-time monitoring
tail -f research_analyzer.log

# Search logs
grep "ERROR" research_analyzer.log
grep "Tier S" research_analyzer.log
```

### Interactive Debugging

**Use Python debugger:**

```python
import pdb

# Set breakpoint
pdb.set_trace()

# Or with pytest
pytest --pdb  # Drop into debugger on failure
```

### Common Issues

**Import errors:**
```bash
# Ensure running as module
python -m main --mode batch

# Check PYTHONPATH
python -c "import sys; print(sys.path)"
```

**Rate limit errors:**
```bash
# Increase rate limit in config
# sources.json: "rate_limit_seconds": 5

# Or reduce concurrency
# Process papers sequentially instead of parallel
```

**AI evaluation failures:**
```bash
# Check API key
echo $ANTHROPIC_API_KEY

# Check response parsing
# Add debug logging in _parse_ai_response()
logger.debug(f"Raw AI response: {text}")
```

---

## Performance Optimization

### Profiling

**Profile code execution:**

```python
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# Run code
await run_batch_analysis(...)

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)  # Top 20 slowest functions
```

### Optimization Tips

**1. Reduce AI API calls:**
- Increase `value_score_minimum` threshold
- Improve signal extraction to filter earlier
- Batch process papers with similar characteristics

**2. Optimize scraping:**
- Use asyncio for parallel fetching
- Respect rate limits but minimize wait time
- Cache responses when appropriate

**3. Memory management:**
- Process papers in batches
- Don't hold all papers in memory
- Use generators for large datasets

**Example batch processing:**

```python
async def process_in_batches(papers: list[Paper], batch_size: int = 10):
    """Process papers in batches to manage memory."""
    for i in range(0, len(papers), batch_size):
        batch = papers[i:i + batch_size]

        for paper in batch:
            await process_paper(paper)

        # Clear batch from memory
        del batch
```

---

## Code Review Checklist

Before submitting code:

- [ ] **Tests written** and passing
- [ ] **Type hints** added to all functions
- [ ] **Docstrings** added with examples
- [ ] **Formatted** with ruff
- [ ] **Linted** with ruff (no errors)
- [ ] **Type checked** with pyright (no errors)
- [ ] **Logging** added for important steps
- [ ] **Error handling** for expected failures
- [ ] **Performance** considered (no obvious bottlenecks)
- [ ] **Documentation** updated (README, API_REFERENCE, etc.)
- [ ] **Breaking changes** noted in commit message

---

## Resources

- **Python Type Hints:** https://docs.python.org/3/library/typing.html
- **Pytest Documentation:** https://docs.pytest.org/
- **Ruff Documentation:** https://docs.astral.sh/ruff/
- **Anthropic API:** https://docs.anthropic.com/
- **httpx Documentation:** https://www.python-httpx.org/

---

## Getting Help

**Common development questions:**

1. **How do I add a new signal?**
   → See [Adding a New Signal Category](#adding-a-new-signal-category)

2. **How do I create a custom scraper?**
   → See [Creating a New Scraper](#creating-a-new-scraper)

3. **Tests are failing with import errors?**
   → Run as module: `python -m pytest`

4. **How do I test without using real API calls?**
   → Use mocks: See [Mock External APIs](#mock-external-apis)

5. **Type checker complains about dynamic attributes?**
   → Use `# type: ignore[attr-defined]` for known dynamic types

---

**Happy coding! Build something awesome. 🚀**
