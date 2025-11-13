# Quick Start Guide

Get the Research Data Landscape Analyzer running in 5 minutes.

## Prerequisites

- Python 3.11+
- Anthropic API key
- Internet connection

## Setup

### 1. Navigate to Project

```bash
cd /Users/justin/Artifact/amplifier/ai_working/research_data_analyzer
```

### 2. Configure Environment

```bash
# Copy template
cp .env.example .env

# Edit and add your API key
nano .env
```

Required: Set `ANTHROPIC_API_KEY=your_key_here`

### 3. Install Dependencies

From project root (`/Users/justin/Artifact/amplifier`):

```bash
uv add anthropic httpx python-dotenv
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

```bash
# Install from project root
cd /Users/justin/Artifact/amplifier
uv add anthropic httpx python-dotenv
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
- 20-50 papers fetched
- 5-10 papers pass signal filter
- 2-5 findings generated
- ~5 minutes runtime

**Full run (90 days)**:
- 200-500 papers fetched
- 50-100 papers evaluated
- 10-30 findings generated
- ~30-60 minutes runtime

## Next Steps

1. Review findings in `findings/tier_s/` and `findings/tier_a/`
2. Adjust sensitivity in `config/heuristics.json` if needed
3. Enable/disable sources in `config/sources.json`
4. Set up continuous monitoring with Docker (see `docker/README.md`)

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
