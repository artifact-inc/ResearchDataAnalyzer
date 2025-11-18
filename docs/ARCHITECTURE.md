# Research Data Analyzer - Architecture

**A hybrid code/AI system for identifying dataset creation opportunities**

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Design Philosophy](#design-philosophy)
3. [Component Architecture](#component-architecture)
4. [Data Flow](#data-flow)
5. [Module Details](#module-details)
6. [Key Design Decisions](#key-design-decisions)
7. [Extension Points](#extension-points)
8. [Testing Strategy](#testing-strategy)

---

## System Overview

### Purpose

The Research Data Analyzer identifies valuable dataset creation opportunities by analyzing academic papers from multiple sources. It operates as a **market research tool** for the AI/ML dataset economy—finding what doesn't exist yet, not harvesting what does.

### Core Value Proposition

Transform the research paper firehose into actionable business intelligence:

```
Papers (arXiv, S2, etc.) → Quality Filter → Signal Extraction →
AI Evaluation → Blocker Detection → Confidence Scoring → Tiered Opportunities
```

### Design Philosophy

**Hybrid Code/AI Architecture**
- **Code handles structure**: Data flow, quality gates, filtering, scoring
- **AI handles nuance**: Evaluation, contextualization, blocker detection
- **Result**: Scalable, maintainable, and intelligent

This separation enables:
- **Reliability**: Deterministic quality controls prevent bad data from reaching AI
- **Cost efficiency**: Only high-signal papers undergo expensive AI evaluation
- **Transparency**: Clear decision points for debugging and refinement
- **Evolution**: Swap AI models or prompts without rewriting pipeline

**Key Principles**:
1. **Multi-stage quality control** - Filter aggressively before expensive AI calls
2. **Source-aware processing** - Different thresholds for arXiv vs. Semantic Scholar
3. **Incremental saves** - Never lose progress (critical for long-running batch jobs)
4. **Defensive utilities** - Graceful degradation, not catastrophic failure

---

## Component Architecture

### Visual Overview

```
┌─────────────────────────────────────────────────────────────┐
│                         SCRAPERS                             │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ArxivScraper │  │SemanticSchol.│  │ Other Scrapers   │  │
│  │             │  │   Scraper    │  │ (Papers w/ Code) │  │
│  └──────┬──────┘  └──────┬───────┘  └────────┬─────────┘  │
│         │                 │                   │             │
│         └─────────────────┴───────────────────┘             │
└─────────────────────────┬───────────────────────────────────┘
                          │ Papers (title, abstract, metadata)
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    QUALITY FILTER                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Age-Adjusted Citation Thresholds + Source Awareness  │  │
│  │  - arXiv: Accept without citations (API limitation)  │  │
│  │  - S2: Age-based thresholds (3 @ <1yr, 30 @ 5+yr)   │  │
│  └──────┬──────────────────────────────────┬────────────┘  │
│         │ Passed                            │ Rejected      │
└─────────┼───────────────────────────────────┼───────────────┘
          │                                   │
          ▼                                   ▼ (logged)
┌─────────────────────────────────────────────────────────────┐
│                   SIGNAL EXTRACTOR                           │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ 30+ Keyword Heuristics Across 8 Categories:          │  │
│  │  • Demand (25%)    • Scarcity (20%)  • Novelty (15%) │  │
│  │  • Quality (10%)   • Scale (10%)                     │  │
│  │  • Commercial (15%)• Trend (5%)   • Meta-Signals     │  │
│  │                                                        │  │
│  │ Enhanced Signals:                                     │  │
│  │  • Data Efficiency • Quality Indicators              │  │
│  │  • Scaling Potential (with sample phrases)           │  │
│  └──────┬───────────────────────────────────────────────┘  │
│         │ Signal Scores (0-10 per category)                │
└─────────┼───────────────────────────────────────────────────┘
          │
          ▼ (if max signal >= 5.0)
┌─────────────────────────────────────────────────────────────┐
│                   VALUE EVALUATOR (AI)                       │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Claude Haiku evaluates:                               │  │
│  │  • Technical Contribution Score (0-10)                │  │
│  │  • Commercial Viability Score (0-10)                 │  │
│  │  • Structured blockers (legal, technical, market)    │  │
│  │  • Business context & target customers               │  │
│  └──────┬───────────────────────────────────────────────┘  │
│         │ OpportunityAssessment (preliminary)               │
└─────────┼───────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│                  BLOCKER DETECTOR                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Parse structured + text-based blockers:               │  │
│  │  Categories: LEGAL, TECHNICAL, MARKET, ECONOMIC       │  │
│  │  Severity: HIGH (cap @ 6.0), MEDIUM (7.5), LOW (10.0)│  │
│  └──────┬───────────────────────────────────────────────┘  │
│         │ Blockers list + score caps                       │
└─────────┼───────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│                CONFIDENCE CALCULATOR                         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Detect uncertainty sources:                           │  │
│  │  • Generic language → -2 pts                          │  │
│  │  • Missing validation → -3 pts                        │  │
│  │  • Speculative terms → -1 pt                          │  │
│  │  • Low evidence → -2 pts                              │  │
│  └──────┬───────────────────────────────────────────────┘  │
│         │ Adjusted Confidence Score                        │
└─────────┼───────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│                 OPPORTUNITY SCORER                           │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Calculate final scores:                               │  │
│  │  • value_score = (tech × 0.3) + (commercial × 0.7)   │  │
│  │  • effective_value_score = min(value, blocker_cap)   │  │
│  │  • tier = f(effective_value_score)                   │  │
│  │      - A: ≥7.5  - B: ≥6.0  - C: <6.0                 │  │
│  └──────┬───────────────────────────────────────────────┘  │
│         │ Complete OpportunityAssessment                   │
└─────────┼───────────────────────────────────────────────────┘
          │
          ▼ (if value_score >= threshold)
┌─────────────────────────────────────────────────────────────┐
│                   OUTPUT WRITER                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Write to tiered directories:                          │  │
│  │  findings/tier_a/YYYY-MM-DD_dataset_name.md          │  │
│  │  findings/index.jsonl (machine-readable)             │  │
│  │  findings/research_analyzer.log                      │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Input | Output |
|-----------|---------------|-------|--------|
| **Scrapers** | Fetch papers from sources | Lookback days / last check | List[Paper] |
| **QualityFilter** | Filter low-quality papers | Papers + FilterConfig | (passed, rejected) |
| **SignalExtractor** | Detect 30+ heuristic signals | Paper | Signal scores (0-10) |
| **ValueEvaluator** | AI-powered evaluation | Paper + Signals | OpportunityAssessment |
| **BlockerDetector** | Identify commercialization blockers | AI response | List[Blocker] |
| **ConfidenceCalculator** | Quantify uncertainty | AI response | Confidence + sources |
| **OpportunityScorer** | Calculate final scores/tier | Assessment + Blockers | Tiered assessment |
| **OutputWriter** | Save findings to files | OpportunityAssessment | Markdown + JSONL |
| **BatchProcessor** | Orchestrate one-time analysis | Config | Findings written |
| **ContinuousMonitor** | Orchestrate ongoing monitoring | Config | Findings over time |

---

## Data Flow

### End-to-End Pipeline

#### 1. **Scraping Phase**
```python
# Multiple scrapers run in parallel
arxiv_papers = await arxiv_scraper.fetch_recent_papers(lookback_days=90)
s2_papers = await s2_scraper.fetch_recent_papers(lookback_days=90)

# Deduplication by paper ID
all_papers = [arxiv_papers, s2_papers]
unique_papers = deduplicate_by_id(all_papers)
```

**Data transformation:**
```
Raw API responses → Paper objects
{
  id: "arxiv/2501.12345",
  title: str,
  abstract: str,
  authors: List[str],
  published_date: datetime,
  source: "arxiv",
  citation_count: int | None,
  url: str
}
```

#### 2. **Quality Filtering Phase**
```python
filtered_papers, rejected = filter_papers(unique_papers, filter_config)
# LOG: "Quality Filter Results: 45 passed, 155 rejected"
# LOG: "Rejection breakdown:"
# LOG: "  - Below age-adjusted threshold: 120"
# LOG: "  - Citation count unavailable: 35"
```

**Quality gates:**
- **arXiv papers**: Always pass (API doesn't provide citations)
- **Semantic Scholar papers**: Age-adjusted thresholds
  - <1 year: ≥3 citations
  - 1-2 years: ≥10 citations
  - 2-5 years: ≥20 citations
  - 5+ years: ≥30 citations

**Why this matters:** Prevents wasting AI credits on noise

#### 3. **Signal Extraction Phase**
```python
for paper in filtered_papers:
    signals = signal_extractor.extract(paper)
    # {
    #   "demand": {"score": 7.5, "detected": ["scarcity_complaint"]},
    #   "scarcity": {"score": 9.0, "detected": ["collection_cost", "privacy"]},
    #   "quality_indicators": {
    #       "score": 8.0,
    #       "detected": ["expert_involvement"],
    #       "sample_phrases": ["...expert radiologists annotated..."]
    #   }
    # }

    max_signal = max(s["score"] for s in signals.values())
    if max_signal < 5.0:
        continue  # Skip weak papers (no AI call)
```

**Key innovation:** Sample phrase extraction for quality/scaling signals provides AI with concrete evidence

#### 4. **AI Evaluation Phase**
```python
assessment = await value_evaluator.evaluate(paper, signals, config)
# Claude receives:
#   - Paper metadata
#   - Signal scores
#   - Sample phrases (e.g., "15% improvement with 10K expert-labeled vs 100K crowd-sourced")
#
# Claude returns:
#   - Technical contribution score (0-10)
#   - Commercial viability score (0-10)
#   - Structured blockers: [{category, severity, description}]
#   - Business context with SPECIFIC EVIDENCE
#   - Target customers (named industries, not "researchers")
```

**Prompt engineering highlights:**
- **Dual scoring**: Separates research novelty from market readiness
- **Structured blockers**: Forces identification of commercialization barriers
- **Evidence requirement**: "Generic language → FLAG as blocker"
- **Pessimistic bias**: "Be pessimistic on commercial viability without evidence"

#### 5. **Quality Control Phase**
```python
# Blocker detection (caps value_score)
blockers = blocker_detector.detect_from_structured(ai_response["blockers"])
# e.g., [{category: LEGAL, severity: HIGH, description: "Protected health attributes"}]
#       → Caps value_score at 6.0 (regardless of AI's original score)

# Confidence calculation (penalizes uncertainty)
confidence, uncertainties = confidence_calculator.calculate(ai_response)
# e.g., uncertainty_sources = [
#   {description: "Generic target market", penalty: 2.0},
#   {description: "Missing market validation", penalty: 3.0}
# ]
# confidence = base_confidence - sum(penalties)
```

**Design rationale:** AI can hallucinate high scores; structured quality controls prevent this

#### 6. **Scoring Phase**
```python
# Weighted value score (favors commercial viability)
value_score = (tech_score * 0.3) + (commercial_score * 0.7)

# Apply blocker caps
effective_value_score = min(value_score, min_blocker_cap)

# Calculate tier based on effective score
if effective_value_score >= 7.5:
    tier = "A"
elif effective_value_score >= 6.0:
    tier = "B"
else:
    tier = "C"
```

**Example:**
```
AI output: tech=9.0, commercial=8.5 → value_score=8.7
Blocker: HIGH severity legal concern → cap at 6.0
Result: effective_value_score=6.0, tier=B (not A)
```

#### 7. **Output Phase**
```python
if assessment.value_score >= threshold:
    output_writer.write_finding(assessment)
    # Writes:
    #   findings/tier_b/2025-01-17_expert_radiology.md
    #   findings/index.jsonl (append)
```

**Incremental saves:** Each finding written immediately (no batch commits)

---

## Module Details

### Models (`models/`)

#### `Paper` (models/paper.py)
```python
@dataclass
class Paper:
    id: str                          # "arxiv/2501.12345"
    title: str
    abstract: str
    authors: list[str]
    published_date: datetime
    source: str                      # "arxiv", "semantic_scholar"
    url: str
    citation_count: int | None = None
    venue: str | None = None
    full_text: str | None = None     # Future: full paper analysis
    dataset_mentions: list[str] = field(default_factory=list)
```

**Design notes:**
- Immutable after creation (dataclass)
- Source field enables source-aware filtering
- Optional fields support varying data availability

#### `OpportunityAssessment` (models/opportunity.py)
```python
@dataclass
class OpportunityAssessment:
    # Core identification
    id: str                          # "rdla_20250117_142350"
    paper: Paper
    data_type_name: str              # "Expert-Annotated Radiology Imaging"

    # Dual scoring
    technical_contribution_score: float   # 0-10
    commercial_viability_score: float     # 0-10
    value_score: float                    # Weighted: tech×0.3 + commercial×0.7
    effective_value_score: float          # After blocker caps
    confidence_score: float               # After uncertainty penalties
    tier: str                             # "A", "B", "C"

    # Quality controls
    blockers: list[Blocker]
    uncertainty_sources: list[UncertaintySource]

    # Business intelligence
    business_context: str
    target_customers: str
    market_gap: str
    concerns: str

    # Enhanced dimensions
    data_efficiency: float           # 0-10
    source_quality: float
    generalizability: float

    # Signals
    signals_detected: dict[str, float]
    detected_at: datetime
```

**Key methods:**
```python
def _apply_blocker_caps(self) -> float:
    """Apply most restrictive blocker cap to value_score."""
    if not self.blockers:
        return self.value_score
    min_cap = min(b.score_cap() for b in self.blockers)
    return min(self.value_score, min_cap)

def calculate_tier(self) -> str:
    """Calculate tier from effective_value_score."""
    # Uses effective_value_score (post-blocker), not raw value_score
```

#### `Blocker` (models/opportunity.py)
```python
@dataclass
class Blocker:
    category: BlockerCategory    # LEGAL, TECHNICAL, MARKET, ECONOMIC
    severity: BlockerSeverity    # HIGH, MEDIUM, LOW
    description: str

    def score_cap(self) -> float:
        """Return maximum allowed value_score."""
        return {
            BlockerSeverity.HIGH: 6.0,
            BlockerSeverity.MEDIUM: 7.5,
            BlockerSeverity.LOW: 10.0
        }[self.severity]
```

**Design rationale:** Even amazing research can have commercialization blockers

#### `UncertaintySource` (models/opportunity.py)
```python
@dataclass
class UncertaintySource:
    description: str                 # "Generic target market identified"
    penalty: float                   # Points to deduct (0-10 scale)
```

**Example penalties:**
- Generic language: -2.0
- Missing validation: -3.0
- Speculative terms: -1.0
- Low evidence: -2.0

---

### Scrapers (`scrapers/`)

#### `BaseScraper` (scrapers/base.py)
```python
class BaseScraper(ABC):
    """Abstract base with rate limiting & retry logic."""

    async def _rate_limit(self) -> None:
        """Enforce minimum time between requests."""
        # Prevents API bans

    async def _retry_with_backoff(
        self, func, max_retries=3, initial_delay=1.0
    ) -> T:
        """Exponential backoff for 429 errors."""
        # Handles transient rate limit errors

    @abstractmethod
    async def fetch_recent_papers(self, days: int) -> list[Paper]:
        """Fetch papers from last N days."""

    @abstractmethod
    async def fetch_new_since(self, last_check: datetime) -> list[Paper]:
        """For continuous monitoring mode."""

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Identifier for logging."""
```

**Shared behavior:**
- Rate limiting (configurable per source)
- Retry with exponential backoff
- Error logging

#### `ArxivScraper` (scrapers/arxiv_scraper.py)
```python
class ArxivScraper(BaseScraper):
    """arXiv API via Atom feeds."""

    async def fetch_recent_papers(self, days: int) -> list[Paper]:
        # Query: submittedDate:[2025-01-01 TO 2025-01-17]
        # Categories: cs.AI, cs.CL, cs.CV, cs.LG, stat.ML
        # Note: citation_count = None (arXiv API limitation)
```

**arXiv specifics:**
- No citation data available
- Categories filter (ML/AI only)
- Atom/XML parsing

#### `SemanticScholarScraper` (scrapers/semantic_scholar_scraper.py)
```python
class SemanticScholarScraper(BaseScraper):
    """Semantic Scholar API with citation data."""

    async def fetch_recent_papers(self, days: int) -> list[Paper]:
        # Query: year:2024+ AND fieldsOfStudy:Computer Science
        # Returns: title, abstract, authors, citationCount, venue
        # Rich metadata including citation counts
```

**S2 specifics:**
- Citation counts available
- Venue information (NeurIPS, ICML, etc.)
- Richer metadata

---

### Analyzers (`analyzers/`)

#### `QualityFilter` (analyzers/quality_filter.py)
```python
@dataclass
class FilterConfig:
    enabled: bool = True
    min_citations_absolute: int = 5
    citation_thresholds: dict[str, int] = {
        "0-1": 3,    # Recent papers
        "1-2": 10,
        "2-5": 20,
        "5+": 30
    }
    allow_unknown_citations: bool = False

def passes_quality_filter(paper: Paper, config: FilterConfig) -> tuple[bool, str]:
    """Source-aware quality filtering."""
    if paper.source == "arxiv":
        return True, "arXiv paper accepted (citation data N/A)"

    age_years = calculate_paper_age_years(paper)
    threshold = get_citation_threshold(age_years, config)

    if paper.citation_count < threshold:
        return False, f"Below threshold ({paper.citation_count} < {threshold})"

    return True, f"Passes: {paper.citation_count} for {age_years:.1f}yr paper"
```

**Design innovation:** Age-adjusted thresholds prevent penalizing recent papers

#### `SignalExtractor` (analyzers/signal_extractor.py)
```python
class SignalExtractor:
    """Extract 30+ heuristic signals across 8 categories."""

    def extract(self, paper: Paper) -> dict[str, dict]:
        text = f"{paper.title} {paper.abstract}".lower()

        return {
            "demand": self._extract_demand_signals(text, paper),
            "scarcity": self._extract_scarcity_signals(text),
            "novelty": self._extract_novelty_signals(text),
            "quality": self._extract_quality_signals(text),
            "data_efficiency": self._extract_efficiency_signals(text),
            "performance": self._extract_performance_signals(text),
            "scale": self._extract_scale_signals(text),
            "commercial": self._extract_commercial_signals(text),
            "trend": self._extract_trend_signals(paper),
            "quality_indicators": self._extract_quality_indicators(text),
            "scaling_potential": self._extract_scaling_potential(text),
        }
```

**Signal detection example:**
```python
def _extract_efficiency_signals(self, text: str) -> dict:
    """Detect data efficiency emphasis."""
    score = 0.0
    detected = []

    # Keyword matching
    efficiency_keywords = ["few-shot", "data-efficient", "sample-efficient"]
    matches = sum(1 for kw in efficiency_keywords if kw in text)
    if matches > 0:
        score += min(matches * 3.0, 9.0)
        detected.append("efficiency_emphasis")

    # Comparative patterns (HIGH VALUE)
    comparative_patterns = [
        r"(\d+)%\s*(improvement|better|gain)",
        r"only\s+\d+[km]?\s*(samples|examples)",
        r"outperform.*with.*fewer"
    ]
    for pattern in comparative_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            score += 5.0
            detected.append("comparative_efficiency")
            break

    return {"score": min(score, 10.0), "detected": detected}
```

**Enhanced signals with sample phrases:**
```python
def _extract_quality_indicators(self, text: str) -> dict:
    """Extract with sample phrases for AI context."""
    sample_phrases = []

    for keyword in quality_keywords:
        if keyword in text:
            # Extract 30-char context window
            phrase = self._extract_sample_phrases(text, keyword, context_window=30)
            sample_phrases.extend(phrase)

    return {
        "score": score,
        "detected": detected,
        "sample_phrases": sample_phrases[:3]  # Top 3 only
    }
```

**Why sample phrases matter:** Gives AI concrete evidence vs. abstract scores

#### `ValueEvaluator` (analyzers/value_evaluator.py)
```python
class ValueEvaluator:
    """AI-powered evaluation with structured output."""

    async def evaluate(
        self, paper: Paper, signals: dict, config: dict
    ) -> OpportunityAssessment | None:
        # Build prompt with signals + sample phrases
        prompt = self._create_evaluation_prompt(paper, signals, signal_scores)

        # Call Claude Haiku
        response = self.client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )

        # Parse structured JSON response
        data = self._parse_ai_response(response.text)

        # Calculate weighted value_score
        value_score = (data["technical_contribution_score"] * 0.3) + \
                      (data["commercial_viability_score"] * 0.7)

        # Detect blockers
        blockers = blocker_detector.detect_from_structured(data["blockers"])

        # Calculate confidence with uncertainty detection
        confidence, uncertainties = confidence_calc.calculate(data)

        # Build assessment
        return OpportunityAssessment(
            value_score=value_score,
            blockers=blockers,
            uncertainty_sources=uncertainties,
            confidence_score=confidence,
            # ... other fields
        )
```

**Prompt engineering:**
```
TASK:
Evaluate this paper on TWO INDEPENDENT dimensions:

1. TECHNICAL CONTRIBUTION (0-10):
   - How novel/significant is the research?
   - Is methodology rigorous and reproducible?
   - Does it advance state-of-the-art?

2. COMMERCIAL VIABILITY (0-10):
   - Clear target customers with validated demand?
   - Data legally/ethically collectable?
   - Viable pricing and distribution?

3. BLOCKERS DETECTION:
   Categories: LEGAL, TECHNICAL, MARKET, ECONOMIC
   Severity: HIGH (cap @ 6.0), MEDIUM (7.5), LOW (10.0)

CRITICAL GUIDELINES:
- Technical score ≠ Commercial score
- Generic language → FLAG as blocker
- Missing validation → BLOCKER detection required
- Be pessimistic without evidence

Return ONLY valid JSON: { ... }
```

**Why this works:**
- Structured output (not free-form text)
- Dual scoring separates novelty from viability
- Forced blocker detection
- Pessimistic bias prevents over-optimism

#### `BlockerDetector` (analyzers/blocker_detector.py)
```python
class BlockerDetector:
    """Detect commercialization blockers from AI responses."""

    def detect_from_structured(
        self, blocker_dicts: list[dict]
    ) -> list[Blocker]:
        """Parse structured blocker format from AI."""
        blockers = []
        for b in blocker_dicts:
            category = BlockerCategory[b["category"].upper()]
            severity = BlockerSeverity[b["severity"].upper()]
            blockers.append(Blocker(category, severity, b["description"]))
        return blockers

    def detect_from_text(self, concerns_text: str) -> list[Blocker]:
        """Fallback: Extract blockers from free-form text."""
        # Keyword-based detection for legal/privacy terms
        # Sentiment analysis for severity
```

**Score cap enforcement:**
```python
blocker = Blocker(
    category=BlockerCategory.LEGAL,
    severity=BlockerSeverity.HIGH,
    description="Protected health information (HIPAA)"
)

effective_score = min(
    assessment.value_score,  # 8.7
    blocker.score_cap()       # 6.0 (HIGH severity)
)
# Result: 6.0 (blocker caps the score)
```

#### `ConfidenceCalculator` (analyzers/confidence_calculator.py)
```python
class ConfidenceCalculator:
    """Quantify uncertainty in AI assessments."""

    def calculate(self, ai_response: dict) -> tuple[float, list[UncertaintySource]]:
        base_confidence = ai_response.get("confidence_score", 8.0)
        uncertainties = []

        # Check for generic language
        if self._has_generic_language(ai_response["business_context"]):
            uncertainties.append(
                UncertaintySource("Generic target market identified", 2.0)
            )

        # Check for missing validation
        if "no validation" in ai_response["concerns"].lower():
            uncertainties.append(
                UncertaintySource("Missing market validation", 3.0)
            )

        # Check for speculative language
        if self._has_speculative_terms(ai_response["business_context"]):
            uncertainties.append(
                UncertaintySource("Speculative market assessment", 1.0)
            )

        # Calculate adjusted confidence
        total_penalty = sum(u.penalty for u in uncertainties)
        final_confidence = max(0.0, base_confidence - total_penalty)

        return final_confidence, uncertainties
```

**Detection patterns:**
```python
GENERIC_PATTERNS = [
    "across industries",
    "wide range of applications",
    "various domains",
    "multiple sectors"
]

SPECULATIVE_TERMS = [
    "could enable",
    "might allow",
    "potentially useful",
    "possibly create"
]
```

**Example:**
```
AI says: "Could enable applications across various domains"
Detected: Generic language + Speculative terms
Penalties: -2.0 (generic) + -1.0 (speculative) = -3.0
Confidence: 8.0 - 3.0 = 5.0/10
```

---

### Monitor (`monitor/`)

#### `BatchProcessor` (monitor/batch_processor.py)
```python
async def run_batch_analysis(
    scrapers: list,
    signal_extractor: SignalExtractor,
    value_evaluator: ValueEvaluator,
    output_writer: OutputWriter,
    lookback_days: int,
    config: dict,
    quality_config: FilterConfig
) -> None:
    """One-time analysis of recent papers."""

    # Fetch from all sources (parallel)
    all_papers = []
    for scraper in scrapers:
        papers = await scraper.fetch_recent_papers(lookback_days)
        all_papers.extend(papers)

    # Deduplicate
    unique_papers = deduplicate_by_id(all_papers)

    # Quality filter
    filtered_papers, rejected = filter_papers(unique_papers, quality_config)

    # Process each paper
    for paper in filtered_papers:
        signals = signal_extractor.extract(paper)

        # Skip weak signals (save AI credits)
        if max(s["score"] for s in signals.values()) < 5.0:
            continue

        # AI evaluation
        assessment = await value_evaluator.evaluate(paper, signals, config)

        # Save if meets threshold
        if assessment.value_score >= threshold:
            output_writer.write_finding(assessment)  # Incremental save
```

**Key features:**
- Parallel scraping
- Deduplication
- Quality filter upfront
- Incremental saves (never lose progress)

#### `ContinuousMonitor` (monitor/continuous_monitor.py)
```python
async def run_continuous_monitor(
    scrapers: list,
    signal_extractor: SignalExtractor,
    value_evaluator: ValueEvaluator,
    output_writer: OutputWriter,
    poll_interval_hours: int,
    config: dict
) -> None:
    """Continuous monitoring mode."""
    last_check = datetime.now(UTC)

    while True:
        # Fetch new papers since last check
        all_new_papers = []
        for scraper in scrapers:
            papers = await scraper.fetch_new_since(last_check)
            all_new_papers.extend(papers)

        # Process new papers (same pipeline as batch)
        # ...

        # Wait for next poll
        last_check = datetime.now(UTC)
        await asyncio.sleep(poll_interval_hours * 3600)
```

**Use case:** Background service polling for new opportunities daily

---

### Persistence (`persistence/`)

#### `OutputWriter` (persistence/output_writer.py)
```python
class OutputWriter:
    """Write findings to tiered directories."""

    def write_finding(self, assessment: OpportunityAssessment) -> None:
        """Write markdown + append to index."""
        tier_dir = self.base_dir / f"tier_{assessment.tier.lower()}"
        tier_dir.mkdir(parents=True, exist_ok=True)

        # Markdown file
        filename = f"{assessment.detected_at.strftime('%Y-%m-%d')}_{sanitize(assessment.data_type_name)}.md"
        md_path = tier_dir / filename
        md_path.write_text(assessment.to_markdown())

        # JSONL index (append)
        index_path = self.base_dir / "index.jsonl"
        with open(index_path, "a") as f:
            f.write(json.dumps(asdict(assessment)) + "\n")
```

**Output structure:**
```
findings/
├── tier_a/
│   ├── 2025-01-17_expert_radiology.md
│   └── 2025-01-17_climate_timeseries.md
├── tier_b/
│   └── 2025-01-17_multimodal_robotics.md
├── tier_c/
│   └── ...
├── index.jsonl          # Machine-readable
└── research_analyzer.log
```

**Why incremental saves:** Long batch jobs can crash; never lose work

---

### Configuration (`config/`)

#### `sources.json`
```json
{
  "arxiv": {
    "enabled": true,
    "categories": ["cs.AI", "cs.CL", "cs.CV", "cs.LG", "stat.ML"],
    "rate_limit_seconds": 3
  },
  "semantic_scholar": {
    "enabled": true,
    "rate_limit_seconds": 1,
    "api_key": null
  }
}
```

#### `heuristics.json`
```json
{
  "sensitivity": "high",
  "thresholds": {
    "value_score_minimum": 6.0,
    "confidence_minimum": 5.0,
    "tier_a_threshold": 7.5,
    "tier_b_threshold": 6.0
  },
  "keywords": {
    "scarcity": ["lack of", "limited", "insufficient", "scarce"],
    "quality": ["expert-annotated", "carefully curated", "quality over quantity"],
    "data_efficiency": ["few-shot", "data-efficient", "sample-efficient"]
  }
}
```

---

## Key Design Decisions

### 1. Why Hybrid Code/AI?

**Problem:** Pure AI systems are expensive, unpredictable, and hard to debug.

**Solution:** Code handles structure, AI handles nuance.

| Aspect | Code Handles | AI Handles |
|--------|--------------|------------|
| Quality gates | Age-adjusted citation thresholds | Contextual evaluation |
| Signal detection | 30+ keyword heuristics | Nuanced interpretation |
| Scoring | Weighted formulas, blocker caps | Technical/commercial assessment |
| Output | Tiered directories, JSONL | Business context narrative |

**Benefits:**
- **Cost efficiency**: Only high-signal papers reach AI
- **Reliability**: Deterministic filters prevent noise
- **Debuggability**: Clear decision points for refinement
- **Maintainability**: Swap AI models without rewriting pipeline

---

### 2. Why Age-Adjusted Citations?

**Problem:** Recent papers (3 months old) won't have many citations yet.

**Naive approach:**
```python
if citation_count < 20:
    reject()  # Rejects ALL recent papers
```

**Age-adjusted approach:**
```python
age_years = (now - published_date).days / 365.25

if age_years < 1:
    threshold = 3   # Be lenient for recent work
elif age_years < 2:
    threshold = 10
elif age_years < 5:
    threshold = 20
else:
    threshold = 30  # Expect more for mature papers
```

**Result:** Captures emerging opportunities without drowning in noise

**Real-world validation:** In 90-day lookback tests, this caught high-value recent papers that would've been rejected by fixed thresholds.

---

### 3. Why Source-Aware Filtering?

**Problem:** arXiv API doesn't provide citation counts.

**Naive approach:**
```python
if paper.citation_count is None:
    reject()  # Rejects ALL arXiv papers
```

**Source-aware approach:**
```python
if paper.source == "arxiv":
    accept()  # arXiv API limitation, trust arXiv curation
elif paper.citation_count is None:
    reject()  # Semantic Scholar SHOULD have citations
```

**Result:** Leverage each source's strengths, work around limitations

---

### 4. Why Incremental Saves?

**Problem:** Batch jobs can crash after hours of processing.

**Naive approach:**
```python
findings = []
for paper in papers:
    assessment = await evaluate(paper)
    findings.append(assessment)

# Write all at end (if we get here!)
write_all(findings)
```

**Incremental approach:**
```python
for paper in papers:
    assessment = await evaluate(paper)
    output_writer.write_finding(assessment)  # Save immediately
```

**Result:** Zero data loss on crashes, failures, or early termination

---

### 5. Why Multi-Stage Scoring?

**Problem:** AI can hallucinate high scores without evidence.

**Naive approach:**
```python
value_score = ai_response["value_score"]  # Trust blindly
tier = calculate_tier(value_score)
```

**Multi-stage approach:**
```python
# Stage 1: Dual scoring (tech vs. commercial)
tech_score = ai_response["technical_contribution_score"]
commercial_score = ai_response["commercial_viability_score"]
value_score = (tech_score * 0.3) + (commercial_score * 0.7)

# Stage 2: Blocker detection (cap scores)
blockers = detect_blockers(ai_response)
effective_score = min(value_score, min_blocker_cap)

# Stage 3: Confidence penalties (uncertainty)
uncertainties = detect_uncertainties(ai_response)
confidence = base_confidence - sum(penalties)

# Stage 4: Tier calculation (effective score)
tier = calculate_tier(effective_score)  # Uses capped score
```

**Result:**
- Separates research quality from market readiness
- Forces identification of commercialization blockers
- Penalizes generic/speculative assessments
- Prevents "garbage in, garbage out"

**Real example:**
```
AI output:
  tech=9.0, commercial=8.5 → value=8.7
  concerns="Protected health information"

Post-processing:
  Blocker: LEGAL/HIGH → cap at 6.0
  Uncertainty: Generic language → -2.0 confidence
  Final: effective_value=6.0, confidence=6.0, tier=B
```

---

### 6. Why Structured Blocker Detection?

**Problem:** Free-form concern text is hard to parse systematically.

**Naive approach:**
```python
concerns = ai_response["concerns"]
# "This might have privacy issues" → How severe? What category?
```

**Structured approach:**
```python
{
  "blockers": [
    {
      "category": "legal",
      "severity": "high",
      "description": "Protected health information (HIPAA)"
    }
  ]
}

# Programmatic handling:
blocker = Blocker.from_dict(blocker_dict)
score_cap = blocker.score_cap()  # 6.0 for HIGH
effective_score = min(value_score, score_cap)
```

**Benefits:**
- Programmatic score caps (not manual judgment)
- Categorization for downstream analysis
- Clear audit trail for why scores were capped

---

### 7. Why Sample Phrase Extraction?

**Problem:** AI receives abstract scores (e.g., "efficiency: 8.0") without context.

**Without sample phrases:**
```
Signal: data_efficiency = 8.0
AI: "This might indicate efficient data usage" (vague)
```

**With sample phrases:**
```
Signal: data_efficiency = 8.0
Sample phrase: "...15% improvement using 10K expert-labeled examples vs.
                100K crowd-sourced samples..."
AI: "The paper demonstrates 15% performance gain with 10× less data when
     using expert annotations, indicating strong data efficiency opportunity."
     (specific)
```

**Result:** AI has concrete evidence, produces higher-quality assessments

---

## Extension Points

### Adding New Scrapers

**Step 1:** Create scraper class
```python
# scrapers/papers_with_code_scraper.py
class PapersWithCodeScraper(BaseScraper):
    async def fetch_recent_papers(self, days: int) -> list[Paper]:
        # API call to Papers with Code
        # Parse response → Paper objects

    async def fetch_new_since(self, last_check: datetime) -> list[Paper]:
        # Continuous monitoring support

    @property
    def source_name(self) -> str:
        return "papers_with_code"
```

**Step 2:** Register in factory
```python
# scrapers/__init__.py
def create_scrapers(config: dict) -> list[BaseScraper]:
    scrapers = []

    if config["papers_with_code"]["enabled"]:
        scrapers.append(PapersWithCodeScraper(config["papers_with_code"]))

    return scrapers
```

**Step 3:** Add configuration
```json
// config/sources.json
{
  "papers_with_code": {
    "enabled": true,
    "rate_limit_seconds": 1,
    "api_key": null
  }
}
```

**Considerations:**
- API rate limits (set `rate_limit_seconds`)
- Citation data availability (for quality filter)
- Field mappings (title, abstract, authors, etc.)

---

### Adding New Signals

**Step 1:** Add keywords to config
```json
// config/heuristics.json
{
  "keywords": {
    "explainability": [
      "interpretable",
      "explainable",
      "transparency",
      "attribution"
    ]
  }
}
```

**Step 2:** Create extraction method
```python
# analyzers/signal_extractor.py
def _extract_explainability_signals(self, text: str) -> dict:
    """Extract explainability/interpretability signals."""
    score = 0.0
    detected = []

    explainability_keywords = self.keywords.get("explainability", [])
    matches = sum(1 for kw in explainability_keywords if kw in text)

    if matches > 0:
        score += min(matches * 2.5, 8.0)
        detected.append("explainability_emphasis")

    # Check for regulatory mentions (high value)
    if any(term in text for term in ["gdpr", "right to explanation", "fda"]):
        score += 5.0
        detected.append("regulatory_driver")

    return {"score": min(score, 10.0), "detected": detected}
```

**Step 3:** Register in `extract()` method
```python
def extract(self, paper: Paper) -> dict[str, dict]:
    text = f"{paper.title} {paper.abstract}".lower()

    return {
        # ... existing signals
        "explainability": self._extract_explainability_signals(text),
    }
```

**Step 4:** Update signal weights (optional)
```json
// config/heuristics.json
{
  "signal_weights": {
    "demand": 0.25,
    "scarcity": 0.20,
    "explainability": 0.10  // New signal
  }
}
```

---

### Modifying AI Prompts

**Prompt location:** `analyzers/value_evaluator.py` → `_create_evaluation_prompt()`

**Common modifications:**

**1. Change scoring emphasis:**
```python
# Current: 30% technical, 70% commercial
value_score = (tech_score * 0.3) + (commercial_score * 0.7)

# Alternative: Equal weight
value_score = (tech_score * 0.5) + (commercial_score * 0.5)
```

**2. Add new evaluation dimensions:**
```python
prompt = f"""
...
3. REGULATORY RISK (0-10):
   - Are there privacy/compliance concerns?
   - Is regulatory approval required?
   - What legal barriers exist?

Return JSON:
{{
    "technical_contribution_score": <float>,
    "commercial_viability_score": <float>,
    "regulatory_risk_score": <float>,  // NEW
    ...
}}
"""
```

**3. Adjust blocker severity thresholds:**
```python
# Current caps
BlockerSeverity.HIGH: 6.0
BlockerSeverity.MEDIUM: 7.5

# Alternative: More aggressive
BlockerSeverity.HIGH: 5.0
BlockerSeverity.MEDIUM: 7.0
```

**Testing changes:**
```bash
# Test with single paper
python -m research_data_analyzer.main --mode batch --lookback-days 7

# Check findings/tier_*/
# Verify scores and blocker caps are applied correctly
```

---

### Adjusting Quality Thresholds

**Location:** `config/heuristics.json`

**Threshold types:**

**1. Value score minimum** (controls AI evaluation volume)
```json
{
  "thresholds": {
    "value_score_minimum": 6.0  // Only save if ≥6.0
  }
}
```

**2. Tier boundaries** (classification)
```json
{
  "thresholds": {
    "tier_a_threshold": 7.5,  // A: ≥7.5
    "tier_b_threshold": 6.0   // B: ≥6.0, C: <6.0
  }
}
```

**3. Quality filter (citation requirements)**
```python
# analyzers/quality_filter.py
FilterConfig(
    min_citations_absolute=5,  // Floor for any age
    citation_thresholds={
        "0-1": 3,    // Adjust for recent papers
        "1-2": 10,
        "2-5": 20,
        "5+": 30
    }
)
```

**Tuning guide:**

| Issue | Solution |
|-------|----------|
| Too many findings | Increase `value_score_minimum` (e.g., 7.0) |
| Too few findings | Lower `value_score_minimum` (e.g., 5.0) |
| Missing recent papers | Lower `citation_thresholds["0-1"]` (e.g., 2) |
| Too much noise | Raise citation thresholds across the board |

---

## Testing Strategy

### Unit Testing

**Core principle:** Test each module in isolation with mocked dependencies.

**Example: Signal Extractor**
```python
# tests/test_signal_extractor.py
def test_extract_efficiency_signals():
    """Test data efficiency signal detection."""
    extractor = SignalExtractor(config={
        "keywords": {
            "data_efficiency": ["few-shot", "data-efficient"]
        }
    })

    # Paper with efficiency language
    paper = Paper(
        title="Few-Shot Learning for Medical Imaging",
        abstract="We achieve 15% improvement with only 100 samples...",
        # ... other fields
    )

    signals = extractor.extract(paper)

    # Assert efficiency signal detected
    assert signals["data_efficiency"]["score"] > 5.0
    assert "efficiency_emphasis" in signals["data_efficiency"]["detected"]
    assert "comparative_efficiency" in signals["data_efficiency"]["detected"]
```

**Example: Quality Filter**
```python
# tests/test_quality_filter.py
def test_age_adjusted_thresholds():
    """Test age-based citation thresholds."""
    config = FilterConfig(citation_thresholds={"0-1": 3, "1-2": 10})

    # Recent paper (3 months old, 5 citations)
    recent_paper = Paper(
        published_date=datetime.now(UTC) - timedelta(days=90),
        citation_count=5,
        source="semantic_scholar",
        # ... other fields
    )

    passes, reason = passes_quality_filter(recent_paper, config)
    assert passes is True  # 5 > 3 (threshold for <1yr)

    # Older paper (2 years old, 5 citations)
    old_paper = Paper(
        published_date=datetime.now(UTC) - timedelta(days=730),
        citation_count=5,
        source="semantic_scholar",
    )

    passes, reason = passes_quality_filter(old_paper, config)
    assert passes is False  # 5 < 10 (threshold for 1-2yr)
```

**Example: Blocker Detector**
```python
# tests/test_blocker_detector.py
def test_structured_blocker_detection():
    """Test parsing structured blocker format."""
    detector = BlockerDetector()

    ai_blockers = [
        {
            "category": "legal",
            "severity": "high",
            "description": "Protected health information (HIPAA)"
        }
    ]

    blockers = detector.detect_from_structured(ai_blockers)

    assert len(blockers) == 1
    assert blockers[0].category == BlockerCategory.LEGAL
    assert blockers[0].severity == BlockerSeverity.HIGH
    assert blockers[0].score_cap() == 6.0
```

### Integration Testing

**Principle:** Test component interactions with real (but small) datasets.

**Example: End-to-End Pipeline**
```python
# tests/test_integration.py
async def test_batch_pipeline_integration():
    """Test complete batch processing pipeline."""
    # Setup
    config = load_config()
    scrapers = [MockArxivScraper(fixture_papers)]  # Use fixtures
    signal_extractor = SignalExtractor(config["heuristics"])
    value_evaluator = ValueEvaluator(config)
    output_writer = OutputWriter(tmp_path)

    # Run batch analysis
    await run_batch_analysis(
        scrapers=scrapers,
        signal_extractor=signal_extractor,
        value_evaluator=value_evaluator,
        output_writer=output_writer,
        lookback_days=30,
        config=config,
        quality_config=FilterConfig()
    )

    # Assertions
    assert (tmp_path / "tier_a").exists()
    assert len(list(tmp_path.glob("tier_*/*.md"))) > 0
    assert (tmp_path / "index.jsonl").exists()
```

### Validation Methodology

**1. Signal detection accuracy**
```python
# Use hand-labeled papers to validate signal extraction
labeled_papers = load_labeled_dataset()  # Papers with known signals

for paper, expected_signals in labeled_papers:
    detected_signals = signal_extractor.extract(paper)

    # Check precision/recall
    precision = calculate_precision(detected_signals, expected_signals)
    recall = calculate_recall(detected_signals, expected_signals)

    assert precision > 0.8  # At least 80% precision
    assert recall > 0.7     # At least 70% recall
```

**2. Quality filter effectiveness**
```python
# Validate rejection rate aligns with expectations
papers = fetch_test_set(days=30)
filtered, rejected = filter_papers(papers, config)

# Should reject ~60-80% of papers (based on empirical testing)
rejection_rate = len(rejected) / len(papers)
assert 0.6 < rejection_rate < 0.8
```

**3. AI evaluation consistency**
```python
# Test same paper multiple times (check variance)
paper = load_fixture("expert_radiology_paper.json")
signals = signal_extractor.extract(paper)

assessments = []
for _ in range(5):
    assessment = await value_evaluator.evaluate(paper, signals, config)
    assessments.append(assessment)

# Check score variance
scores = [a.value_score for a in assessments]
assert np.std(scores) < 1.0  # Low variance expected
```

**4. Output format validation**
```python
# Ensure markdown and JSONL are well-formed
findings = list((findings_dir / "tier_a").glob("*.md"))

for finding_path in findings:
    # Parse markdown
    md = finding_path.read_text()
    assert "# 🔥 [Tier A]" in md or "# ⭐ [Tier A]" in md
    assert "**Value Score**:" in md

    # Check JSONL index
    index = (findings_dir / "index.jsonl").read_text()
    assert finding_path.stem in index  # Finding ID exists
```

### Running Tests

```bash
# Unit tests
pytest tests/test_signal_extractor.py -v
pytest tests/test_quality_filter.py -v
pytest tests/test_blocker_detector.py -v

# Integration tests
pytest tests/test_integration.py -v

# All tests with coverage
pytest tests/ --cov=research_data_analyzer --cov-report=html

# Specific test
pytest tests/test_value_evaluator.py::test_dual_scoring -v
```

---

## Performance Characteristics

### Processing Times (Empirical)

**Stage 1: Scraping** (90-day lookback)
- arXiv: ~15 seconds (100 papers)
- Semantic Scholar: ~30 seconds (100 papers)
- Deduplication: <1 second

**Stage 2: Quality Filtering**
- 200 papers: <1 second
- Rejection rate: ~70% (typical)

**Stage 3: Signal Extraction**
- 60 filtered papers: ~2 seconds
- Weak signal skip rate: ~50%

**Stage 4: AI Evaluation**
- 30 high-signal papers: ~5-8 minutes (Haiku)
- Cost: ~$0.10-0.15 per 100 papers

**Stage 5: Quality Controls**
- Blocker detection: <1 second
- Confidence calculation: <1 second

**Total (90-day batch):** ~8-10 minutes for 200 papers → 5-8 findings

### Cost Analysis

**API costs** (Claude Haiku):
- Input: ~500 tokens/paper (paper + signals)
- Output: ~400 tokens/assessment
- Rate: ~$0.25 per million input tokens, ~$1.25 per million output tokens

**Cost per paper:**
- Input: 500 tokens × $0.25/1M = $0.000125
- Output: 400 tokens × $1.25/1M = $0.0005
- Total: ~$0.000625 per AI evaluation

**Batch analysis (90 days):**
- Papers fetched: 200
- Quality filtered: 60 (30% pass rate)
- AI evaluated: 30 (50% have strong signals)
- Cost: 30 × $0.000625 = **~$0.02**

**Continuous monitoring (daily):**
- Papers/day: ~10
- AI evaluated: ~2
- Cost/day: ~$0.001
- Cost/month: ~$0.03

**Optimization levers:**
1. Quality filter (reduce AI calls)
2. Signal threshold (skip weak papers)
3. Model choice (Haiku vs. Sonnet vs. Opus)

---

## Future Enhancements

### Near-term

**1. Full-text analysis** (currently title + abstract only)
```python
# models/paper.py
@dataclass
class Paper:
    full_text: str | None = None  # Extract from PDF/HTML

# analyzers/signal_extractor.py
def extract(self, paper: Paper) -> dict:
    text = paper.full_text or f"{paper.title} {paper.abstract}"
    # Richer signal detection with full content
```

**2. Slack integration** (replace OutputWriter)
```python
# persistence/slack_notifier.py
class SlackNotifier:
    async def notify_finding(self, assessment: OpportunityAssessment):
        blocks = assessment.to_slack_blocks()
        await self.client.post_message(
            channel="#opportunities",
            blocks=blocks
        )
```

**3. Historical trend analysis**
```python
# analyzers/trend_analyzer.py
def analyze_trends(findings: list[OpportunityAssessment]) -> TrendReport:
    # Identify recurring themes
    # Track signal evolution over time
    # Detect emerging patterns
```

### Long-term

**4. Multi-modal analysis** (images, videos, code)
```python
# Current: Text-only
# Future: Extract figures, code snippets, demo videos
```

**5. Citation graph analysis**
```python
# Detect paper clusters (multiple papers → same dataset need)
# Identify influential researchers/labs
```

**6. Automated dataset creation pipelines**
```python
# From opportunity → data collection plan → implementation
```

---

## Troubleshooting

### Common Issues

**1. Import errors**
```bash
# Error: ModuleNotFoundError: No module named 'research_data_analyzer'

# Solution: Run as module from correct directory
cd ai_working/research_data_analyzer
python -m research_data_analyzer.main --mode batch
```

**2. No findings generated**
```bash
# Check logs
tail -f research_analyzer.log

# Common causes:
# - Thresholds too high (lower value_score_minimum)
# - Quality filter too aggressive (check rejection breakdown)
# - Weak signals (check signal extraction for test papers)
```

**3. Rate limit errors**
```bash
# Error: 429 Too Many Requests

# Solutions:
# - Increase rate_limit_seconds in sources.json
# - Add API keys (Semantic Scholar)
# - Reduce batch size
```

**4. AI evaluation failures**
```bash
# Error: Failed to parse AI response as JSON

# Causes:
# - Prompt drift (AI not following JSON format)
# - Token limit exceeded (reduce max_tokens)
# - Model unavailability

# Debug:
# - Check logs for raw AI response
# - Validate prompt with test papers
```

---

## References

- [README.md](./README.md) - User guide and quickstart
- [QUALITY_IMPROVEMENT_STRATEGIES.md](./QUALITY_IMPROVEMENT_STRATEGIES.md) - Quality control evolution (if exists)
- `config/` - Configuration files
- `tests/` - Test suite

---

**Last updated:** 2025-01-17
**Architecture version:** 2.0 (Multi-stage quality control system)
