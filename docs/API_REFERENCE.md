# API Reference

Complete API documentation for all public interfaces in the Research Data Analyzer.

---

## Table of Contents

1. [Models](#models)
   - [Paper](#paper)
   - [OpportunityAssessment](#opportunityassessment)
   - [Blocker](#blocker)
   - [UncertaintySource](#uncertaintysource)
2. [Analyzers](#analyzers)
   - [SignalExtractor](#signalextractor)
   - [ValueEvaluator](#valueevaluator)
   - [QualityFilter](#qualityfilter)
   - [BlockerDetector](#blockerdetector)
   - [ConfidenceCalculator](#confidencecalculator)
3. [Scrapers](#scrapers)
   - [BaseScraper](#basescraper)
   - [ArxivScraper](#arxivscraper)
   - [SemanticScholarScraper](#semanticscholarsc raper)
4. [Processors](#processors)
   - [BatchProcessor](#batchprocessor)
   - [ContinuousMonitor](#continuousmonitor)
5. [Output](#output)
   - [OutputWriter](#outputwriter)

---

## Models

### Paper

Represents a research paper from any source.

**Module:** `models.paper`

**Definition:**
```python
@dataclass
class Paper:
    id: str                           # Unique paper identifier
    title: str                        # Paper title
    abstract: str                     # Paper abstract
    authors: list[str]                # List of author names
    published_date: datetime          # Publication date
    source: str                       # Source name (e.g., "arXiv", "Semantic Scholar")
    url: str                          # Paper URL
    citation_count: int | None        # Citation count (if available)
    venue: str | None                 # Publication venue (if available)
    full_text: str | None             # Full text (if available)
    dataset_mentions: list[str]       # Extracted dataset mentions
```

**Creation Example:**
```python
from datetime import datetime, UTC
from models.paper import Paper

paper = Paper(
    id="arxiv:2025.12345",
    title="Novel Approach to Climate Modeling",
    abstract="We present a new method for...",
    authors=["Smith, J.", "Doe, A."],
    published_date=datetime.now(UTC),
    source="arXiv",
    url="https://arxiv.org/abs/2025.12345",
    citation_count=15,
    venue="NeurIPS 2025"
)
```

---

### OpportunityAssessment

Represents a commercial dataset opportunity identified from a paper.

**Module:** `models.opportunity`

**Definition:**
```python
@dataclass
class OpportunityAssessment:
    # Core fields
    id: str                                    # Unique finding ID (e.g., "rdla_20250117_143022")
    paper: Paper                               # Source paper
    data_type_name: str                        # Concise dataset name
    business_context: str                      # Commercial value explanation
    value_score: float                         # AI-evaluated value (0-10)
    confidence_score: float                    # Confidence in assessment (0-10)
    tier: str                                  # Tier: S, A, B, C, D
    signals_detected: dict[str, float]         # Signal category scores
    detected_at: datetime                      # Detection timestamp

    # Optional enrichment fields
    target_customers: str = ""                 # Identified customer segments
    market_gap: str = ""                       # Market need description
    concerns: str = ""                         # Risks and limitations

    # Enhanced dimensions
    data_efficiency: float = 0.0               # Data efficiency score (0-10)
    source_quality: float = 0.0                # Source quality score (0-10)
    generalizability: float = 0.0              # Generalization potential (0-10)

    # Dual scoring (v2.0+)
    technical_contribution_score: float = 0.0   # Research quality (0-10)
    commercial_viability_score: float = 0.0     # Market readiness (0-10)

    # Quality controls (v2.0+)
    blockers: list[Blocker] = field(default_factory=list)
    uncertainty_sources: list[UncertaintySource] = field(default_factory=list)
    effective_value_score: float = 0.0          # value_score after blocker caps
```

**Key Methods:**

#### `calculate_tier() -> str`
Calculate tier based on effective_value_score.

```python
assessment.calculate_tier()  # Returns: "S", "A", "B", "C", or "D"
```

**Tier Thresholds:**
- **Tier S**: effective_value_score >= 9.0
- **Tier A**: effective_value_score >= 7.5
- **Tier B**: effective_value_score >= 6.0
- **Tier C**: effective_value_score < 6.0

#### `to_markdown() -> str`
Generate markdown report for the finding.

```python
markdown = assessment.to_markdown()
# Returns formatted markdown with:
# - Tier emoji and header
# - Paper metadata
# - Business context
# - Scoring details
# - Detected signals
# - Blockers (if any)
# - Concerns (if any)
```

**Example Output:**
```markdown
# 🔥 [Tier S] Expert-Annotated Radiology Dataset

**Paper**: https://arxiv.org/abs/2025.12345
**Published**: 2025-01-15
...
```

---

### Blocker

Represents a commercialization blocker that caps the effective value score.

**Module:** `models.opportunity`

**Definition:**
```python
class BlockerCategory(Enum):
    LEGAL = "legal"          # Privacy, IP, regulatory
    TECHNICAL = "technical"  # Validation gaps, reproducibility
    MARKET = "market"        # Customer access, distribution
    ECONOMIC = "economic"    # Cost structure, pricing viability

class BlockerSeverity(Enum):
    LOW = "low"             # Minor issue, easily addressed
    MEDIUM = "medium"       # Significant concern, needs investigation
    HIGH = "high"           # Fundamental barrier, major resolution required

@dataclass
class Blocker:
    category: BlockerCategory
    severity: BlockerSeverity
    description: str

    def score_cap(self) -> float:
        """Return maximum value_score allowed for this blocker."""
        # HIGH: caps at 6.0
        # MEDIUM: caps at 7.5
        # LOW: caps at 10.0 (no effective cap)
```

**Usage Example:**
```python
from models.opportunity import Blocker, BlockerCategory, BlockerSeverity

blocker = Blocker(
    category=BlockerCategory.LEGAL,
    severity=BlockerSeverity.HIGH,
    description="Contains protected health attributes (HIPAA violation)"
)

max_score = blocker.score_cap()  # Returns: 6.0
```

---

### UncertaintySource

Represents a source of uncertainty that reduces confidence score.

**Module:** `models.opportunity`

**Definition:**
```python
@dataclass
class UncertaintySource:
    description: str    # What causes the uncertainty
    penalty: float      # Confidence points to deduct (0-10 scale)
```

**Usage Example:**
```python
from models.opportunity import UncertaintySource

uncertainty = UncertaintySource(
    description="No market validation or customer feedback",
    penalty=2.0
)

# Applied automatically by ConfidenceCalculator
# confidence_score = 10.0 - sum(all penalties)
```

---

## Analyzers

### SignalExtractor

Extracts heuristic signals from paper text using keyword matching.

**Module:** `analyzers.signal_extractor`

**Constructor:**
```python
SignalExtractor(config: dict)
```

**Parameters:**
- `config`: Heuristics configuration dict with keyword lists

**Methods:**

#### `extract(paper: Paper) -> dict[str, dict]`

Extract all signal categories from a paper.

```python
extractor = SignalExtractor(config)
signals = extractor.extract(paper)

# Returns dict with keys:
# - demand: Demand signals
# - scarcity: Scarcity signals
# - novelty: Novelty signals
# - quality: Quality signals
# - data_efficiency: Efficiency signals
# - performance: Performance signals
# - scale: Scale signals
# - commercial: Commercial viability signals
# - trend: Trend signals
# - quality_indicators: Quality assurance signals
# - scaling_potential: Scaling/generalization signals
```

**Signal Structure:**
```python
{
    "demand": {
        "score": 7.5,                    # 0-10 score
        "detected": ["scarcity_complaint", "synthetic_workaround"]
    },
    "scarcity": {
        "score": 9.0,
        "detected": ["collection_cost", "privacy_restriction"]
    },
    # ... other categories
}
```

**Signal Categories:**

| Category | Weight | Description |
|----------|--------|-------------|
| demand | 25% | Data scarcity complaints, synthetic workarounds |
| scarcity | 20% | Collection costs, privacy/legal restrictions |
| novelty | 15% | First-of-kind, multimodal, emerging domains |
| quality | 10% | Annotation quality, expert involvement |
| scale | 10% | Performance scaling, pre-training opportunities |
| commercial | 15% | Industry mentions, regulatory needs |
| trend | 5% | Citation count, major venue publication |
| data_efficiency | - | Efficiency emphasis, comparative claims |
| performance | - | Performance improvements, SOTA claims |
| quality_indicators | - | QA processes, validation methods |
| scaling_potential | - | Transfer learning, cross-domain applicability |

---

### ValueEvaluator

AI-powered commercial value evaluation using Claude.

**Module:** `analyzers.value_evaluator`

**Constructor:**
```python
ValueEvaluator(config: dict)
```

Requires `ANTHROPIC_API_KEY` environment variable.

**Methods:**

#### `async evaluate(paper: Paper, signals: dict[str, dict], config: dict) -> OpportunityAssessment | None`

Evaluate a paper with AI and quality controls.

```python
evaluator = ValueEvaluator(config)
assessment = await evaluator.evaluate(paper, signals, config)

if assessment:
    print(f"Value: {assessment.value_score:.1f}")
    print(f"Confidence: {assessment.confidence_score:.1f}")
    print(f"Tier: {assessment.tier}")
```

**AI Evaluation Process:**
1. Create evaluation prompt with dual scoring requirements
2. Call Claude API (claude-3-haiku-20240307)
3. Parse JSON response
4. Detect blockers from structured/text data
5. Calculate confidence with uncertainty detection
6. Calculate weighted value_score (30% technical, 70% commercial)
7. Apply blocker caps to get effective_value_score
8. Calculate tier based on effective score

**Returns:**
- `OpportunityAssessment` if successful
- `None` if evaluation fails

---

### QualityFilter

Pre-filter papers before AI evaluation to reduce costs.

**Module:** `analyzers.quality_filter`

**Configuration:**
```python
@dataclass
class FilterConfig:
    min_abstract_length: int = 100
    min_author_count: int = 1
    max_age_days: int = 365
    require_venue: bool = False
    min_citations: int = 0
```

**Function:**
```python
def filter_papers(
    papers: list[Paper],
    config: FilterConfig
) -> tuple[list[Paper], list[Paper]]:
    """Filter papers by quality criteria.

    Returns:
        Tuple of (passing papers, rejected papers)
    """
```

**Usage Example:**
```python
from analyzers.quality_filter import FilterConfig, filter_papers

config = FilterConfig(
    min_abstract_length=150,
    min_citations=5,
    max_age_days=180
)

passed, rejected = filter_papers(papers, config)
print(f"{len(passed)} passed, {len(rejected)} rejected")
```

---

### BlockerDetector

Detects commercialization blockers from AI evaluation text.

**Module:** `analyzers.blocker_detector`

**Methods:**

#### `detect_from_structured(blocker_data: list[dict]) -> list[Blocker]`

Extract blockers from structured Claude output (preferred method).

```python
detector = BlockerDetector()

blocker_data = [
    {
        "category": "legal",
        "severity": "high",
        "description": "Protected health attributes (HIPAA)"
    }
]

blockers = detector.detect_from_structured(blocker_data)
```

#### `detect_from_text(concerns: str) -> list[Blocker]`

Extract blockers from free-text concerns using pattern matching (fallback).

```python
detector = BlockerDetector()
concerns = "Privacy violations and unclear licensing make this risky."
blockers = detector.detect_from_text(concerns)
```

**Detected Patterns:**

High-severity legal blockers:
- "protected attributes"
- "privacy violations"
- "GDPR"
- "regulatory approval required"

High-severity technical blockers:
- "cannot reproduce"
- "no validation data"
- "synthetic data only"

(See `BlockerDetector.BLOCKER_PATTERNS` for full list)

---

### ConfidenceCalculator

Calculates confidence scores based on uncertainty sources.

**Module:** `analyzers.confidence_calculator`

**Methods:**

#### `calculate(evaluation_data: dict) -> tuple[float, list[UncertaintySource]]`

Calculate confidence and identify uncertainty sources.

```python
calculator = ConfidenceCalculator()

evaluation_data = {
    "business_opportunity": "High demand across industries...",
    "concerns": "Market validation unclear",
    "market_gap": "Various potential use cases",
    # ...
}

confidence, uncertainties = calculator.calculate(evaluation_data)
# confidence: 10.0 - sum(penalties), clamped to [0, 10]
# uncertainties: List of UncertaintySource objects
```

**Uncertainty Penalties:**

| Source | Penalty | Detection Pattern |
|--------|---------|-------------------|
| missing_market_validation | 2.0 | "no market validation", "market unclear" |
| vague_business_opportunity | 1.5 | "high demand across industries", "various use cases" |
| severe_concerns_understated | 2.5 | "however significant", "but critical" |
| no_customer_validation | 2.0 | "no customer feedback", "hypothetical customers" |
| unclear_pricing | 1.0 | "pricing uncertain", "monetization unclear" |
| hypothetical_use_cases | 2.0 | "potential use", "could apply" |

---

## Scrapers

### BaseScraper

Abstract base class for all paper scrapers.

**Module:** `scrapers.base`

**Definition:**
```python
class BaseScraper(ABC):
    def __init__(self, config: dict) -> None:
        """Initialize with configuration."""

    @abstractmethod
    async def fetch_recent_papers(self, days: int) -> list[Paper]:
        """Fetch papers from last N days."""

    @abstractmethod
    async def fetch_new_since(self, last_check: datetime) -> list[Paper]:
        """Fetch papers published since timestamp."""

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Return the name of this source."""
```

**Built-in Features:**
- Rate limiting (`_rate_limit()`)
- Exponential backoff retry for 429 errors (`_retry_with_backoff()`)

**Creating a Custom Scraper:**

```python
from scrapers.base import BaseScraper
from models.paper import Paper

class MyCustomScraper(BaseScraper):
    @property
    def source_name(self) -> str:
        return "My Custom Source"

    async def fetch_recent_papers(self, days: int) -> list[Paper]:
        await self._rate_limit()  # Enforce rate limiting

        # Implement your fetching logic
        papers = await self._fetch_from_api(days)
        return papers

    async def fetch_new_since(self, last_check: datetime) -> list[Paper]:
        # Implementation for continuous monitoring
        pass
```

---

### ArxivScraper

Scraper for arXiv.org papers.

**Module:** `scrapers.arxiv`

**Configuration:**
```python
{
    "enabled": true,
    "categories": ["cs.AI", "cs.CL", "cs.CV", "cs.LG"],
    "rate_limit_seconds": 3
}
```

**Categories:**
- `cs.AI` - Artificial Intelligence
- `cs.CL` - Computation and Language
- `cs.CV` - Computer Vision
- `cs.LG` - Machine Learning

**Usage:**
```python
from scrapers.arxiv import ArxivScraper

config = {"categories": ["cs.AI"], "rate_limit_seconds": 3}
scraper = ArxivScraper(config)

papers = await scraper.fetch_recent_papers(days=30)
```

---

### SemanticScholarScraper

Scraper for Semantic Scholar papers with citation data.

**Module:** `scrapers.semantic_scholar`

**Configuration:**
```python
{
    "enabled": true,
    "rate_limit_seconds": 1,
    "api_key": null  # Optional: for higher rate limits
}
```

**Features:**
- Citation count data
- Venue information
- Author details

**Usage:**
```python
from scrapers.semantic_scholar import SemanticScholarScraper

config = {"rate_limit_seconds": 1}
scraper = SemanticScholarScraper(config)

papers = await scraper.fetch_recent_papers(days=30)

for paper in papers:
    print(f"{paper.title}: {paper.citation_count} citations")
```

---

## Processors

### BatchProcessor

One-time batch analysis of recent papers.

**Module:** `monitor.batch_processor`

**Function:**
```python
async def run_batch_analysis(
    scrapers: list[BaseScraper],
    signal_extractor: SignalExtractor,
    value_evaluator: ValueEvaluator,
    output_writer: OutputWriter,
    lookback_days: int,
    config: dict,
    quality_config: FilterConfig
) -> None:
    """Run one-time batch analysis."""
```

**Process:**
1. Fetch papers from all scrapers
2. Deduplicate by paper ID
3. Apply quality filter
4. Extract signals from each paper
5. Skip papers with weak signals (max < 5.0)
6. Evaluate promising papers with AI
7. Save findings that meet threshold

**Usage:**
```python
await run_batch_analysis(
    scrapers=[arxiv_scraper, s2_scraper],
    signal_extractor=extractor,
    value_evaluator=evaluator,
    output_writer=writer,
    lookback_days=90,
    config=config,
    quality_config=filter_config
)
```

---

### ContinuousMonitor

Continuous monitoring mode for ongoing discovery.

**Module:** `monitor.continuous_monitor`

**Function:**
```python
async def run_continuous_monitor(
    scrapers: list[BaseScraper],
    signal_extractor: SignalExtractor,
    value_evaluator: ValueEvaluator,
    output_writer: OutputWriter,
    poll_interval_hours: int,
    config: dict,
    quality_config: FilterConfig
) -> None:
    """Run continuous monitoring loop."""
```

**Process:**
1. Initialize last_check timestamp
2. Loop indefinitely:
   - Fetch new papers since last_check
   - Process like batch mode
   - Sleep for poll_interval_hours
   - Update last_check

**Usage:**
```python
await run_continuous_monitor(
    scrapers=[arxiv_scraper, s2_scraper],
    signal_extractor=extractor,
    value_evaluator=evaluator,
    output_writer=writer,
    poll_interval_hours=24,
    config=config,
    quality_config=filter_config
)
```

---

## Output

### OutputWriter

Writes opportunity findings to markdown files with tier-based organization.

**Module:** `persistence.output_writer`

**Constructor:**
```python
OutputWriter(base_dir: str = "./findings")
```

**Directory Structure:**
```
findings/
├── tier_s/
├── tier_a/
├── tier_b/
├── tier_c/
├── tier_d/
└── index.jsonl
```

**Methods:**

#### `write_finding(assessment: OpportunityAssessment) -> Path`

Write a finding to file and append to index.

```python
writer = OutputWriter(base_dir="./findings")
filepath = writer.write_finding(assessment)
# Returns: Path("findings/tier_a/2025-01-17_expert_radiology.md")
```

**File Naming:**
```
{timestamp}_{sanitized_data_type_name}.md
```

Example: `2025-01-17_expert_annotated_radiology.md`

**Index Format (`index.jsonl`):**

Each line is a JSON object:
```json
{
  "id": "rdla_20250117_143022",
  "tier": "A",
  "data_type_name": "Expert-Annotated Radiology Dataset",
  "value_score": 8.2,
  "confidence_score": 7.5,
  "paper_url": "https://arxiv.org/abs/2025.12345",
  "paper_title": "Novel Radiology Dataset...",
  "detected_at": "2025-01-17T14:30:22+00:00"
}
```

**Reading the Index:**

```python
import json
from pathlib import Path

index_path = Path("findings/index.jsonl")

findings = []
with open(index_path) as f:
    for line in f:
        findings.append(json.loads(line))

# Filter by tier
tier_a = [f for f in findings if f["tier"] == "A"]
```

---

## Common Usage Patterns

### Complete Analysis Pipeline

```python
from analyzers import SignalExtractor, ValueEvaluator
from analyzers.quality_filter import FilterConfig, filter_papers
from scrapers.arxiv import ArxivScraper
from persistence.output_writer import OutputWriter
from monitor.batch_processor import run_batch_analysis

# Initialize components
scraper = ArxivScraper({"categories": ["cs.AI"], "rate_limit_seconds": 3})
extractor = SignalExtractor(heuristics_config)
evaluator = ValueEvaluator(evaluator_config)
writer = OutputWriter("./findings")

filter_config = FilterConfig(min_abstract_length=150, min_citations=5)

# Run analysis
await run_batch_analysis(
    scrapers=[scraper],
    signal_extractor=extractor,
    value_evaluator=evaluator,
    output_writer=writer,
    lookback_days=30,
    config=main_config,
    quality_config=filter_config
)
```

### Custom Signal Processing

```python
# Extract and filter signals
extractor = SignalExtractor(config)
signals = extractor.extract(paper)

# Get top signal categories
top_signals = {
    cat: data for cat, data in signals.items()
    if data["score"] >= 7.0
}

# Check for meta-patterns
has_perfect_storm = (
    signals["demand"]["score"] >= 7.0 and
    signals["scarcity"]["score"] >= 7.0 and
    signals["commercial"]["score"] >= 7.0
)
```

### Blocker Analysis

```python
from analyzers.blocker_detector import BlockerDetector
from models.opportunity import BlockerSeverity

detector = BlockerDetector()
blockers = detector.detect_from_text(concerns_text)

# Filter high-severity blockers
critical_blockers = [
    b for b in blockers
    if b.severity == BlockerSeverity.HIGH
]

if critical_blockers:
    print("Critical blockers detected:")
    for blocker in critical_blockers:
        print(f"  [{blocker.category.value.upper()}] {blocker.description}")
```

---

## Error Handling

All async methods may raise:
- `httpx.HTTPStatusError` - HTTP errors from scrapers
- `anthropic.APIError` - AI evaluation errors
- `ValueError` - Configuration errors
- `json.JSONDecodeError` - Response parsing errors

**Best Practices:**

```python
try:
    papers = await scraper.fetch_recent_papers(30)
except httpx.HTTPStatusError as e:
    if e.response.status_code == 429:
        # Rate limited - handled by retry logic
        pass
    else:
        logger.error(f"HTTP error: {e}")
except Exception as e:
    logger.error(f"Unexpected error: {e}")
```

---

## Type Hints

All functions use Python 3.11+ type hints:

```python
def extract(self, paper: Paper) -> dict[str, dict]
async def evaluate(self, paper: Paper, signals: dict[str, dict], config: dict) -> OpportunityAssessment | None
def filter_papers(papers: list[Paper], config: FilterConfig) -> tuple[list[Paper], list[Paper]]
```

Use type checkers like `pyright` or `mypy` for validation.

---

## See Also

- [DEVELOPMENT_GUIDE.md](./DEVELOPMENT_GUIDE.md) - Development setup and testing
- [docs/FINDINGS_FORMAT.md](./docs/FINDINGS_FORMAT.md) - Output format specification
- [CHANGELOG.md](./CHANGELOG.md) - Version history
- [README.md](./README.md) - User guide and quick start
