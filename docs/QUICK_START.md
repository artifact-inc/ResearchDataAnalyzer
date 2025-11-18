# Quick Start Guide

Get the Research Data Landscape Analyzer running in 5 minutes.

**What this tool does:**
Automatically analyzes ML research papers to identify commercial dataset creation opportunities. You'll get tier-ranked findings with business cases, confidence scores, and blocker detection - perfect for market research and opportunity discovery.

## Prerequisites

- **Python 3.11+** installed
- **Anthropic API key** - [Sign up here](https://console.anthropic.com/)
- **uv package manager** (recommended) or pip - [Install uv](https://github.com/astral-sh/uv)
- Internet connection

## Setup

### 1. Navigate to Project

```bash
# From wherever you cloned the amplifier repository
cd ai_working/research_data_analyzer
```

### 2. Configure Environment

```bash
# Copy the environment template
cp .env.example .env

# Edit and add your API key
nano .env  # or use vim, code, etc.
```

Add your Anthropic API key to `.env`:
```bash
ANTHROPIC_API_KEY=your_actual_key_here
```

### 3. Install Dependencies

**Using uv (recommended):**
```bash
# From the amplifier project root directory
cd ../..  # Navigate to amplifier root
uv add anthropic httpx python-dotenv
cd ai_working/research_data_analyzer  # Return to project
```

**Using pip:**
```bash
pip install anthropic httpx python-dotenv
```

## Run

### Quick Test (Last 7 Days)

```bash
python -m research_data_analyzer.main --mode batch --lookback-days 7 --log-level INFO
```

This will:
- Fetch papers from arXiv and Semantic Scholar
- Analyze them for dataset opportunities
- Save findings to `./findings/`
- Take 5-15 minutes depending on number of papers

### Full Analysis (Last 90 Days)

```bash
python -m research_data_analyzer.main --mode batch --lookback-days 90
```

### Continuous Monitoring

```bash
python -m research_data_analyzer.main --mode monitor --poll-interval-hours 24
```

Press Ctrl+C to stop.

## Check Results

```bash
# View findings by tier
ls -R findings/

# Read a specific finding
cat findings/tier_s/2025-*.md | head -50

# Check logs
tail -f research_analyzer.log
```

## Troubleshooting

### "ANTHROPIC_API_KEY not set"

```bash
# Check .env file exists and has key
cat .env | grep ANTHROPIC_API_KEY
```

### "No module named 'anthropic'"

**Using uv:**
```bash
# Navigate to amplifier project root
cd ../../..  # or wherever your amplifier root is
uv add anthropic httpx python-dotenv
```

**Using pip:**
```bash
pip install anthropic httpx python-dotenv
```

### "No module named 'models'" or Import Errors

The project uses relative imports. **Run as a module:**

```bash
# Recommended approach
python -m research_data_analyzer.main --mode batch
```

**Alternative: Set PYTHONPATH**
```bash
# Temporary for current session
export PYTHONPATH="$(pwd):$PYTHONPATH"
python main.py --mode batch

# Or add to ~/.bashrc for permanent setup
echo 'export PYTHONPATH="/path/to/research_data_analyzer:$PYTHONPATH"' >> ~/.bashrc
```

**Verify imports work:**
```bash
python -c "from models.paper import Paper; print('✓ Imports working')"
```

### No findings generated

Try lowering threshold:
```bash
# Edit config/heuristics.json
# Change "value_score_minimum": 6.0 → 5.0
```

## What to Expect

**First run (7 days)**:
- **Papers fetched**: 20-50 from arXiv and Semantic Scholar
- **Papers evaluated**: 5-10 that pass the quality filter
- **Findings generated**: 2-5 tier-ranked opportunities
- **Runtime**: ~5-10 minutes
- **Cost**: ~$0.10-0.30 in Claude API usage

**Full run (90 days)**:
- **Papers fetched**: 200-500 papers
- **Papers evaluated**: 50-100 papers
- **Findings generated**: 10-30 opportunities
- **Runtime**: ~30-60 minutes
- **Cost**: ~$2-5 in Claude API usage

**What success looks like:**
```bash
# You should see output like this:
INFO - Starting Research Data Landscape Analyzer (batch mode)
INFO - Fetching papers from last 7 days...
INFO - arXiv: Found 25 papers
INFO - Semantic Scholar: Found 18 papers
INFO - Quality Filter: 43 papers → 8 passed (18.6%)
INFO - Evaluating 8 papers with Claude...
INFO - Generated 3 findings: Tier S: 1, Tier A: 2, Tier B: 0
INFO - Findings saved to ./findings/
```

## Verify It's Working

```bash
# Check that findings were created
ls -la findings/

# Should see directory structure:
findings/
├── tier_s/
│   └── 2025-01-17_expert_annotation.md
├── tier_a/
│   ├── 2025-01-17_synthetic_data.md
│   └── 2025-01-17_multimodal_datasets.md
└── index.jsonl

# Read a finding
cat findings/tier_s/*.md
```

## Next Steps

1. **Review your findings**: Start with `findings/tier_s/` (highest value opportunities)
2. **Adjust sensitivity**: Edit `config/heuristics.json` if too many/few findings
   - Lower `value_score_minimum` (e.g., 5.0) for more findings
   - Raise it (e.g., 7.0) for fewer, higher-quality findings
3. **Customize sources**: Edit `config/sources.json` to enable/disable sources or arXiv categories
4. **Set up monitoring**: Use Docker for continuous background monitoring (see `docker/README.md`)
5. **Integrate with your workflow**: See `docs/FINDINGS_FORMAT.md` for integration examples

## Docker Quick Start

```bash
cd docker

# One-time scan
docker-compose --profile batch up analyzer-batch

# Continuous monitoring
docker-compose up -d analyzer
docker-compose logs -f analyzer
```

---

**Need help?** See full [README.md](README.md) or check logs at `research_analyzer.log`
