# Research Data Landscape Analyzer

A market research tool for identifying dataset creation opportunities by analyzing ML research papers.

## 🎯 Purpose

This tool helps you identify valuable dataset types to create by analyzing research papers from multiple sources (arXiv, Semantic Scholar, etc.). It's designed for market research - finding opportunities to CREATE new datasets, not harvesting existing ones.

## 🚀 Quick Start

### 1. Setup

```bash
cd ai_working/research_data_analyzer

# Copy environment template
cp .env.example .env

# Edit .env and add your API keys
nano .env
```

Required environment variables:
- `ANTHROPIC_API_KEY` (required) - For AI evaluation

### 2. Install Dependencies

From project root:
```bash
# Add required packages
uv add anthropic httpx python-dotenv
```

### 3. Run Batch Analysis

```bash
# Analyze last 30 days of papers
python -m research_data_analyzer.main --mode batch --lookback-days 30
```

### 4. Run Continuous Monitoring

```bash
# Monitor for new papers daily
python -m research_data_analyzer.main --mode monitor --poll-interval-hours 24
```

---

## 📊 How It Works

### Data Firehose Approach

The system scrapes papers from multiple sources:
- **arXiv**: ML/AI preprints (cs.AI, cs.CL, cs.CV, cs.LG, etc.)
- **Semantic Scholar**: Academic papers with citation data

### 8 Signal Categories

The analyzer detects **30+ heuristic signals** across 8 categories:

1. **Demand Signals** (weight: 25%)
   - Data scarcity complaints
   - Synthetic data workarounds
   - Multi-paper convergence

2. **Scarcity Signals** (weight: 20%)
   - Collection cost barriers
   - Size limitations
   - Privacy/legal restrictions

3. **Novelty Signals** (weight: 15%)
   - First-of-kind mentions
   - Multimodal combinations
   - Emerging applications

4. **Quality Signals** (weight: 10%)
   - Annotation quality emphasis
   - Expert involvement

5. **Scale Signals** (weight: 10%)
   - Performance scaling
   - Pre-training opportunities

6. **Commercial Viability** (weight: 15%)
   - Industry mentions
   - Regulatory needs
   - Cross-industry use

7. **Trend Signals** (weight: 5%)
   - Publication velocity
   - Major lab adoption
   - High citations

8. **Meta-Signals**
   - "Perfect Storm": Demand + Labs + Industry + Scarcity
   - "Blue Ocean": Novelty + Emerging + No benchmark
   - "Quality Play": Size limits + Quality emphasis
   - "Scale Opportunity": Scaling laws + Pre-training gap

### AI-Powered Evaluation

After extracting signals, Claude evaluates:
- Commercial value (0-10)
- Confidence level (0-10)
- Business context
- Target customers
- Market gaps
- Concerns/risks

### Tiered Output

Findings are organized by tier:
- **Tier S** (9.0+): Immediate high-value opportunities
- **Tier A** (7.5-8.9): Strong opportunities
- **Tier B** (6.0-7.4): Solid opportunities
- **Tier C** (4.0-5.9): Emerging opportunities
- **Tier D** (<4.0): Low viability

---

## 📁 Output Format

```
findings/
├── tier_s/
│   ├── 2025-01-13_expert_radiology.md
│   └── 2025-01-13_climate_timeseries.md
├── tier_a/
│   └── ...
├── tier_b/
│   └── ...
├── index.jsonl          # Machine-readable index
└── research_analyzer.log # Execution logs
```

### Example Finding

```markdown
# 🔥 [Tier S] Expert-Annotated Radiology Imaging

**Paper**: https://arxiv.org/abs/2025.12345
**Published**: 2025-01-10
**Citations**: 45
**Source**: arXiv (cs.CV)

---

## 💰 Business Opportunity

This paper highlights the critical need for high-quality, expert-annotated 
chest X-ray datasets. The authors achieved 15% performance improvement using 
a carefully curated 10K-image dataset compared to existing 100K+ datasets 
with crowd-sourced labels...

**Target Customers**: Medical AI startups, hospital AI initiatives
**Market Gap**: High-quality expert annotations for radiological imaging

---

## 📊 Scoring

**Value Score**: 9.2/10
**Confidence**: 8.5/10
**Tier**: S

**Signals Detected**:
- Scarcity: 9.0
- Quality: 9.5
- Commercial: 8.5
- Trend: 7.5

---

*Detected: 2025-01-13 10:23:45 UTC*
*Finding ID: rdla_20250113_001*
```

---

## ⚙️ Configuration

### Adjust Sensitivity

Edit `config/heuristics.json`:

```json
{
  "sensitivity": "high",
  "thresholds": {
    "value_score_minimum": 6.0,  // Lower = more findings
    "confidence_minimum": 5.0,
    "tier_s_threshold": 9.0,
    "tier_a_threshold": 7.5,
    "tier_b_threshold": 6.0
  }
}
```

### Enable/Disable Sources

Edit `config/sources.json`:

```json
{
  "arxiv": {
    "enabled": true,
    "categories": ["cs.AI", "cs.CL", "cs.CV", "cs.LG"],
    "rate_limit_seconds": 3
  },
  "semantic_scholar": {
    "enabled": true,
    "rate_limit_seconds": 1
  }
}
```

### Adjust Keywords

Add custom keywords in `config/heuristics.json`:

```json
{
  "keywords": {
    "scarcity": ["lack of", "limited", "scarce", ...],
    "novelty": ["first", "novel", "new", ...],
    "industry": ["real-world", "production", ...]
  }
}
```

---

## 🐳 Docker Deployment

### Using Docker Compose

```bash
cd docker

# Batch mode (one-time scan)
docker-compose --profile batch up analyzer-batch

# Continuous monitoring (background)
docker-compose up -d analyzer

# View logs
docker-compose logs -f analyzer

# Stop monitoring
docker-compose down
```

See `docker/README.md` for comprehensive deployment guide.

---

## 🔧 Command-Line Options

```bash
python -m research_data_analyzer.main --help

Options:
  --mode {batch,monitor}     Operating mode (default: batch)
  --lookback-days N          Days to look back for batch mode (default: 90)
  --poll-interval-hours N    Hours between polls for monitor mode (default: 24)
  --findings-dir PATH        Output directory (default: ./findings)
  --log-level LEVEL          Logging level (default: INFO)
```

### Examples

```bash
# Quick scan of last week
python -m research_data_analyzer.main --mode batch --lookback-days 7

# Hourly monitoring (high frequency)
python -m research_data_analyzer.main --mode monitor --poll-interval-hours 1

# Custom output directory
python -m research_data_analyzer.main --findings-dir /data/opportunities

# Debug mode
python -m research_data_analyzer.main --log-level DEBUG
```

---

## 📈 Usage Tips

### Getting Started

1. **Start with batch mode** to build initial corpus
2. **Review findings** to calibrate sensitivity
3. **Adjust thresholds** in config if too many/few results
4. **Switch to monitor mode** for ongoing discovery

### Optimizing Results

**Too many findings:**
- Increase `value_score_minimum` threshold
- Increase `confidence_minimum` threshold
- Disable weaker sources

**Too few findings:**
- Lower `value_score_minimum` (try 5.0)
- Add more keywords to heuristics
- Enable more arXiv categories

### Managing Costs

Claude API usage depends on:
- Number of papers processed
- Papers passing initial signal filter (>5.0)
- Threshold settings

**To reduce costs:**
- Increase `value_score_minimum` (fewer AI evaluations)
- Increase rate limits (slower but cheaper)
- Run less frequently

---

## 🔮 Future Enhancements

### Slack Integration

The output format is designed for easy Slack integration:

```python
# Each OpportunityAssessment has a to_slack_blocks() method
blocks = assessment.to_slack_blocks()

# Send to Slack (future implementation)
slack_client.post_message(channel="#opportunities", blocks=blocks)
```

When ready, replace `OutputWriter` with a `SlackNotifier` class.

### Additional Data Sources

**Papers with Code Integration** (not yet implemented)

Papers with Code could provide valuable dataset and benchmark information. Potential benefits:
- Dataset popularity metrics
- Benchmark performance trends
- Active research areas

**Implementation considerations:**
- API rate limits and access requirements
- Data quality and coverage assessment
- Integration with existing signal extraction
- Incremental value vs implementation cost

See `config/sources.json` for source configuration pattern. Would follow the same scraper architecture as arXiv and Semantic Scholar implementations.

---

## 🛠️ Extending the System

### Adding New Scrapers

1. Create new scraper in `scrapers/`
2. Inherit from `BaseScraper`
3. Implement required methods
4. Add to `create_scrapers()` in `scrapers/__init__.py`
5. Add configuration in `config/sources.json`

### Adding New Signals

1. Add keywords to `config/heuristics.json`
2. Create detection method in `analyzers/signal_extractor.py`
3. Add to `extract()` method
4. Update signal weights in config

### Custom AI Models

Edit `analyzers/value_evaluator.py` to use different models:

```python
response = self.client.messages.create(
    model="claude-3-opus-20240229",  # More powerful
    # or model="claude-3-haiku-20240307",  # Faster/cheaper
    ...
)
```

---

## 📋 Troubleshooting

### No findings generated

**Check:**
1. Logs for errors: `tail -f research_analyzer.log`
2. API key is set correctly
3. Thresholds aren't too high
4. Papers are being fetched (check logs)

### Rate limit errors

**Solutions:**
- Increase `rate_limit_seconds` in sources config
- Disable sources temporarily
- Add Semantic Scholar API key for higher limits

### Import errors

**Fix:**
- Ensure running from project root
- Check Python path includes parent directory
- Verify all `__init__.py` files exist

**PYTHONPATH Setup:**

The project uses relative imports (e.g., `from models.paper import Paper`). For these to work, the `ai_working/research_data_analyzer` directory must be in Python's import path.

**Option 1: Run as module (recommended)**
```bash
# From ai_working/research_data_analyzer directory
python -m research_data_analyzer.main --mode batch
```

**Option 2: Set PYTHONPATH explicitly**
```bash
# Add to ~/.bashrc or ~/.zshrc
export PYTHONPATH="/Users/justin/Artifact/amplifier/ai_working/research_data_analyzer:$PYTHONPATH"

# Or set temporarily for current session
export PYTHONPATH="$(pwd):$PYTHONPATH"
python main.py --mode batch
```

**Option 3: Use sys.path manipulation** (already implemented)

The project already includes `sys.path` setup in entry point files. If you encounter import errors, verify:
```python
# In main.py, monitor scripts - this should be present
if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
```

**Testing imports:**
```bash
# Verify imports work
python -c "from models.paper import Paper; print('✓ Imports working')"
```

---

## 📚 Architecture

```
research_data_analyzer/
├── models/              # Data structures (Paper, OpportunityAssessment)
├── config/              # Configuration loaders
├── scrapers/            # Paper sources (arXiv, S2, etc.)
├── analyzers/           # Signal extraction + AI evaluation
├── persistence/         # Output writing
├── monitor/             # Batch & continuous modes
└── main.py              # Entry point
```

**Design Principles:**
- Modular architecture ("bricks and studs")
- Code for structure, AI for intelligence
- Ethical scraping (rate limits, robots.txt)
- Incremental saves (no data loss)
- Slack-ready output format

---

## 🤝 Contributing

This is a market research tool with a solid ethical foundation:
- ✅ Identifies opportunities to CREATE datasets
- ✅ Respects rate limits and ToS
- ✅ Public data only
- ❌ No harvesting of existing datasets
- ❌ No unauthorized data collection

---

## 📄 License

Part of the Amplifier project. See main project LICENSE.

---

## 🆘 Support

For issues:
1. Check logs: `research_analyzer.log`
2. Review configuration files
3. Ensure API keys are valid
4. Verify network connectivity
5. See Docker deployment guide for containerized troubleshooting

---

**Built with**: Python 3.11+, Claude AI, httpx, python-dotenv
**Pattern**: Amplifier CLI Tool (hybrid code/AI architecture)
