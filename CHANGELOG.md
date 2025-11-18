# Changelog

All notable changes to the Research Data Analyzer will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [2.0.0] - 2025-11-17

Major quality control improvements with dual scoring system, blocker detection, and confidence recalibration.

### Added

#### Dual Scoring System
- **Technical Contribution Score** (0-10): Evaluates research quality, novelty, and reproducibility
- **Commercial Viability Score** (0-10): Evaluates market readiness, customer clarity, and business viability
- Weighted value calculation: 30% technical + 70% commercial
- Independent scoring prevents research novelty from masking commercial weaknesses

#### Blocker Detection
- **Automated blocker detection** from AI evaluation text
- **Four blocker categories**: Legal, Technical, Market, Economic
- **Three severity levels**:
  - HIGH: Caps effective score at 6.0
  - MEDIUM: Caps effective score at 7.5
  - LOW: No effective cap
- **Structured blocker output** from Claude with category/severity/description
- **Fallback text-based detection** using pattern matching
- Blockers visible in markdown output with emoji indicators

#### Confidence Recalibration
- **Uncertainty source detection** from evaluation text
- **Penalty-based confidence calculation**: 10.0 - sum(penalties)
- **10 uncertainty patterns** detected:
  - Missing market validation (-2.0)
  - Vague business language (-1.5)
  - Severe concerns understated (-2.5)
  - No customer validation (-2.0)
  - Unclear pricing (-1.0)
  - Hypothetical use cases (-2.0)
  - And more...
- Uncertainty sources listed in markdown output

#### Effective Score System
- **effective_value_score**: Value score after applying blocker caps
- **Tier calculation** based on effective score (not raw value score)
- Prevents high technical scores from inflating tier when commercialization blockers exist

#### Enhanced AI Prompts
- Explicit dual scoring instructions in evaluation prompt
- Blocker detection guidelines with examples
- Generic language detection patterns
- Evidence requirements for business claims
- Pessimistic bias on commercial viability without validation

### Changed

- **Tier calculation**: Now uses effective_value_score instead of value_score
- **Confidence scoring**: Now calculated algorithmically instead of AI-provided
- **AI model**: Explicitly using claude-3-haiku-20240307 for evaluations
- **Markdown output**: Added blocker section, uncertainty section, dual scores section

### Fixed

- Addressed issue where high research novelty masked poor commercial viability
- Prevented generic business language ("high demand across industries") from inflating scores
- Improved detection of unvalidated market assumptions

### Technical Details

#### New Classes/Modules
- `models.opportunity.Blocker` - Blocker dataclass with category, severity, description
- `models.opportunity.BlockerCategory` - Enum for blocker categories
- `models.opportunity.BlockerSeverity` - Enum for severity levels
- `models.opportunity.UncertaintySource` - Uncertainty source with penalty
- `analyzers.blocker_detector.BlockerDetector` - Blocker extraction logic
- `analyzers.confidence_calculator.ConfidenceCalculator` - Confidence scoring logic

#### Modified Classes
- `OpportunityAssessment`: Added fields for technical_contribution_score, commercial_viability_score, blockers, uncertainty_sources, effective_value_score
- `OpportunityAssessment.__post_init__`: Auto-calculates effective_value_score
- `OpportunityAssessment.calculate_tier()`: Uses effective_value_score
- `OpportunityAssessment.to_markdown()`: Includes blocker and uncertainty sections

#### API Changes
- `ValueEvaluator.evaluate()`: Now returns assessments with dual scores and quality controls
- Evaluation prompt significantly expanded with dual scoring requirements

---

## [1.2.0] - 2025-11-15

Enhanced signal detection with quality indicators and scaling potential.

### Added

#### New Signal Categories
- **quality_indicators**: QA processes, validation methods, inter-annotator agreement
- **scaling_potential**: Transfer learning, cross-domain applicability, generalization

#### Sample Phrase Extraction
- Extract context around detected keywords (30-character window)
- Include up to 3 sample phrases per signal category
- Pass phrases to AI for better context in evaluation

#### Enhanced Dimensions
- **data_efficiency**: How efficiently the dataset enables learning
- **source_quality**: Quality and reliability of data sources
- **generalizability**: Potential for transfer and cross-domain use

### Changed

- **Signal extraction**: Added phrase extraction to quality and scaling signals
- **AI prompt**: Enhanced with sample phrases from quality/scaling signals
- **Markdown output**: Display enhanced dimensions in scoring section

---

## [1.1.0] - 2025-11-14

Quality filter and performance improvements.

### Added

#### Pre-Evaluation Quality Filter
- `analyzers.quality_filter.FilterConfig` - Configurable filter criteria
- `analyzers.quality_filter.filter_papers()` - Filter function
- Criteria: abstract length, author count, age, venue, citations
- Reduces API costs by filtering low-quality papers before AI evaluation

#### Performance Signals
- Detect quantified performance improvements
- Extract SOTA claims
- Identify comparative results

### Changed

- **Batch processor**: Apply quality filter before signal extraction
- **Logging**: Enhanced with filter statistics

### Fixed

- Handle papers with missing citation_count gracefully
- Improved error handling in scraper retry logic

---

## [1.0.0] - 2025-11-13

Initial public release.

### Added

#### Core Features
- **8 Signal Categories**: Demand, Scarcity, Novelty, Quality, Scale, Commercial, Trend, Efficiency
- **AI-Powered Evaluation**: Claude-based commercial value assessment
- **Tiered Output**: S/A/B/C/D tier organization
- **Multiple Sources**: arXiv and Semantic Scholar scrapers

#### Signal Extraction
- `analyzers.signal_extractor.SignalExtractor` - Keyword-based signal detection
- 30+ heuristic patterns across signal categories
- Weighted scoring system
- Meta-pattern detection (Perfect Storm, Blue Ocean, Quality Play, Scale Opportunity)

#### AI Evaluation
- `analyzers.value_evaluator.ValueEvaluator` - Claude integration
- Value score (0-10) and confidence (0-10)
- Business context generation
- Target customer identification
- Market gap analysis
- Concerns/risks assessment

#### Data Sources
- `scrapers.arxiv.ArxivScraper` - arXiv API integration
  - Categories: cs.AI, cs.CL, cs.CV, cs.LG, cs.RO, stat.ML
  - Rate limiting (3s default)
- `scrapers.semantic_scholar.SemanticScholarScraper` - Semantic Scholar API
  - Citation data
  - Venue information
  - Rate limiting (1s default)

#### Processing Modes
- **Batch Mode**: One-time analysis of recent papers
- **Continuous Mode**: Ongoing monitoring with polling
- Configurable lookback/poll intervals
- Deduplication across sources

#### Output
- `persistence.output_writer.OutputWriter` - Markdown and JSON output
- Tier-based directory structure
- Human-readable markdown files
- Machine-readable index.jsonl
- Slack-ready format

#### Configuration
- `config/heuristics.json` - Keyword lists and signal weights
- `config/sources.json` - Scraper configuration
- Environment-based API keys
- Configurable thresholds

#### Quality Features
- Rate limiting with exponential backoff
- Retry logic for 429 errors
- Graceful error handling
- Detailed logging
- Incremental saves (no data loss)

### Documentation

- README.md - User guide with quick start
- ARCHITECTURE.md - System design and principles
- QUICK_START.md - Getting started guide
- docker/README.md - Docker deployment guide
- Tests with pytest

### Technical Stack

- Python 3.11+
- Anthropic Claude API (claude-3-haiku)
- httpx for async HTTP
- python-dotenv for config
- pytest for testing

---

## [0.2.0] - 2025-11-12 (Beta)

Internal testing release.

### Added

- Basic signal extraction (5 categories)
- Claude integration for evaluation
- arXiv scraper only
- Markdown output only
- Manual testing

### Known Issues

- No confidence calibration
- Generic business language not flagged
- High false positive rate
- No blocker detection

---

## [0.1.0] - 2025-11-10 (Alpha)

Initial prototype.

### Added

- Proof of concept
- Basic keyword matching
- Simple scoring
- arXiv scraper prototype

---

## Migration Guides

### Migrating from 1.x to 2.0

**Breaking Changes:**

1. **Tier calculation changed**:
   ```python
   # OLD (v1.x): Tier based on value_score
   tier = calculate_tier(assessment.value_score)

   # NEW (v2.0): Tier based on effective_value_score
   tier = assessment.calculate_tier()  # Uses effective_value_score
   ```

2. **New required fields in OpportunityAssessment**:
   ```python
   # v2.0 assessments include:
   assessment.technical_contribution_score  # NEW
   assessment.commercial_viability_score    # NEW
   assessment.blockers                      # NEW (list)
   assessment.uncertainty_sources           # NEW (list)
   assessment.effective_value_score         # NEW
   ```

3. **Markdown format expanded**:
   - New "Blockers Detected" section
   - New "Effective Score" line
   - New "Dual Scoring" section
   - New "Uncertainty Sources" section

**Non-Breaking Changes:**

- Existing index.jsonl entries still compatible
- Old markdown files still readable (just missing new sections)
- API signatures unchanged (new fields have defaults)

**Recommended Actions:**

1. **Update integrations** to handle new markdown sections
2. **Use effective_value_score** for tier filtering in production
3. **Review blockers** in existing high-tier findings
4. **Re-run analysis** on critical opportunities with v2.0 for quality control

**Example Migration:**

```python
# OLD v1.x code
def filter_tier_s(findings):
    return [f for f in findings if f.value_score >= 9.0]

# NEW v2.0 code
def filter_tier_s(findings):
    # Use effective_value_score to account for blockers
    return [f for f in findings if f.effective_value_score >= 9.0]
    # Or just check tier directly
    return [f for f in findings if f.tier == "S"]
```

---

## Deprecation Notices

### Version 2.0

None.

### Version 1.0

None.

---

## Roadmap

### Planned for 3.0

**Enhanced Quality Controls:**
- Comparative validation (check against existing datasets)
- Market size estimation
- Competition analysis
- Pricing model suggestions

**Additional Data Sources:**
- Papers with Code integration
- Google Scholar metadata
- OpenReview papers
- Conference proceedings

**Improved AI:**
- Multi-model evaluation (Claude + GPT-4)
- Confidence intervals instead of point estimates
- Evidence extraction and citation
- Structured reasoning traces

**Better Output:**
- Interactive HTML reports
- Dashboard for findings management
- Slack bot integration
- Email digest automation

### Under Consideration

- Real-time monitoring (WebSocket-based)
- Custom signal definition UI
- Dataset marketplace integration
- Automated customer outreach templates
- Competitive landscape analysis

---

## Support

For issues, questions, or feature requests:

1. Check logs: `research_analyzer.log`
2. Review configuration files
3. Ensure API keys are valid
4. See [DEVELOPMENT_GUIDE.md](./DEVELOPMENT_GUIDE.md) for debugging
5. Open issue on GitHub (when available)

---

## Contributors

- Research Data Analyzer development team
- Part of the Amplifier project

---

## License

See main project LICENSE file.

---

**Note:** This changelog follows [Keep a Changelog](https://keepachangelog.com/) conventions and [Semantic Versioning](https://semver.org/).
