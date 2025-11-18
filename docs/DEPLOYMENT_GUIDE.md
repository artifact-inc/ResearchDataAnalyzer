# Deployment Guide

Comprehensive guide for deploying Research Data Landscape Analyzer in local, Docker, and production environments.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Deployment](#local-deployment)
3. [Docker Deployment](#docker-deployment)
4. [Production Configuration](#production-configuration)
5. [Scaling Considerations](#scaling-considerations)
6. [Monitoring and Observability](#monitoring-and-observability)
7. [Troubleshooting](#troubleshooting)
8. [Backup and Disaster Recovery](#backup-and-disaster-recovery)

---

## Prerequisites

### Required

- **Python 3.11+**: Check with `python --version` or `python3 --version`
- **Anthropic API Key**: Sign up at https://console.anthropic.com
- **uv** (recommended) or pip for dependency management

### Optional

- **Docker** and **Docker Compose**: For containerized deployment
- **Semantic Scholar API Key**: Higher rate limits (free at https://www.semanticscholar.org/product/api)

### System Requirements

**Minimum:**
- 2 CPU cores
- 4 GB RAM
- 10 GB disk space

**Recommended:**
- 4+ CPU cores
- 8 GB RAM
- 50 GB disk space (for findings storage)

---

## Local Deployment

### 1. Clone Repository

```bash
cd /path/to/amplifier
cd ai_working/research_data_analyzer
```

### 2. Set Up Virtual Environment

**Using uv (recommended):**
```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync
```

**Using pip:**
```bash
# Create virtual environment
python3 -m venv .venv

# Activate environment
source .venv/bin/activate  # Linux/Mac
# OR
.venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
# Copy template
cp .env.example .env

# Edit with your API keys
nano .env
```

**Required Environment Variables:**
```env
# REQUIRED: Anthropic API key for AI evaluation
ANTHROPIC_API_KEY=sk-ant-api03-xxxxx

# OPTIONAL: Semantic Scholar API key (higher rate limits)
SEMANTIC_SCHOLAR_API_KEY=your_key_here

# Operating mode (batch or monitor)
MODE=batch

# Batch mode: days to look back
LOOKBACK_DAYS=90

# Monitor mode: hours between checks
POLL_INTERVAL_HOURS=24

# Log level
LOG_LEVEL=INFO
```

### 4. Verify Installation

```bash
# Test imports
python -c "import research_data_analyzer; print('✓ Imports work')"

# Check configuration
python -m research_data_analyzer.main --help
```

### 5. Run Batch Mode

```bash
# Analyze last 30 days
python -m research_data_analyzer.main --mode batch --lookback-days 30

# With verbose logging
python -m research_data_analyzer.main --mode batch --lookback-days 30 --log-level DEBUG
```

**Output:**
- Findings written to `findings/tier_A/`, `findings/tier_B/`, etc.
- Session state saved to `.sessions/`
- Logs to console

### 6. Run Continuous Monitor

```bash
# Monitor with 24-hour poll interval
python -m research_data_analyzer.main --mode monitor --poll-interval-hours 24

# Monitor with 6-hour interval
python -m research_data_analyzer.main --mode monitor --poll-interval-hours 6
```

**Behavior:**
- Runs continuously in foreground
- Checks for new papers at specified interval
- Saves findings incrementally
- Use Ctrl+C to stop

### 7. Run as Background Service (Linux/Mac)

**Using nohup:**
```bash
nohup python -m research_data_analyzer.main --mode monitor --poll-interval-hours 24 \
  > analyzer.log 2>&1 &

# Get process ID
echo $! > analyzer.pid

# Check logs
tail -f analyzer.log

# Stop service
kill $(cat analyzer.pid)
```

**Using systemd:**
```bash
# Create service file
sudo nano /etc/systemd/system/research-analyzer.service
```

```ini
[Unit]
Description=Research Data Landscape Analyzer
After=network.target

[Service]
Type=simple
User=yourusername
WorkingDirectory=/path/to/ai_working/research_data_analyzer
Environment="PATH=/path/to/.venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/path/to/.venv/bin/python -m research_data_analyzer.main --mode monitor --poll-interval-hours 24
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable research-analyzer
sudo systemctl start research-analyzer

# Check status
sudo systemctl status research-analyzer

# View logs
sudo journalctl -u research-analyzer -f
```

---

## Docker Deployment

### 1. Prerequisites

```bash
# Install Docker
curl -fsSL https://get.docker.com | sh

# Install Docker Compose (if not included)
sudo apt-get install docker-compose-plugin

# Verify installation
docker --version
docker compose version
```

### 2. Setup Environment

```bash
cd ai_working/research_data_analyzer

# Copy .env template
cp .env.example .env

# Edit with your API keys
nano .env
```

### 3. Run Batch Mode (One-Time Scan)

```bash
cd docker
docker compose --profile batch up analyzer-batch

# With custom lookback period
LOOKBACK_DAYS=7 docker compose --profile batch up analyzer-batch
```

**What happens:**
- Builds Docker image (first run only)
- Scans papers from past N days
- Saves findings to `../findings/`
- Container exits when complete

### 4. Run Continuous Monitoring (Background Service)

```bash
cd docker
docker compose up -d analyzer

# View logs
docker compose logs -f analyzer

# Stop monitoring
docker compose down
```

### 5. Docker Volume Mounts

The container uses these volumes:

| Host Path | Container Path | Purpose | Mode |
|-----------|---------------|---------|------|
| `../findings` | `/app/findings` | Output directory | Read-Write |
| `../config` | `/app/config` | Configuration | Read-Only |
| `../.sessions` | `/app/.sessions` | Session state | Read-Write |
| `../.env` | `/app/.env` | Environment vars | Read-Only |

### 6. Docker Management Commands

**View running containers:**
```bash
docker ps
```

**Enter running container:**
```bash
docker exec -it research_data_analyzer /bin/bash
```

**View logs:**
```bash
# All logs
docker compose logs analyzer

# Last 100 lines
docker compose logs --tail=100 analyzer

# Follow in real-time
docker compose logs -f analyzer
```

**Restart container:**
```bash
docker compose restart analyzer
```

**Rebuild after code changes:**
```bash
docker compose down
docker compose build --no-cache
docker compose up -d analyzer
```

**Clean up:**
```bash
# Stop and remove containers
docker compose down

# Remove all Docker resources
docker compose down --volumes --rmi all
```

---

## Production Configuration

### 1. API Key Management

**Use secrets management:**

**AWS Secrets Manager:**
```bash
# Store secret
aws secretsmanager create-secret \
  --name research-analyzer/anthropic-key \
  --secret-string "sk-ant-api03-xxxxx"

# Retrieve in startup script
export ANTHROPIC_API_KEY=$(aws secretsmanager get-secret-value \
  --secret-id research-analyzer/anthropic-key \
  --query SecretString \
  --output text)
```

**HashiCorp Vault:**
```bash
# Store secret
vault kv put secret/research-analyzer \
  anthropic_key="sk-ant-api03-xxxxx"

# Retrieve
export ANTHROPIC_API_KEY=$(vault kv get -field=anthropic_key \
  secret/research-analyzer)
```

**Docker Secrets:**
```yaml
# docker-compose.yml
services:
  analyzer:
    secrets:
      - anthropic_key
    environment:
      - ANTHROPIC_API_KEY_FILE=/run/secrets/anthropic_key

secrets:
  anthropic_key:
    external: true
```

### 2. Rate Limiting Configuration

Edit `config/sources.json`:

```json
{
  "arxiv": {
    "enabled": true,
    "rate_limit_seconds": 3,
    "max_results_per_query": 100
  },
  "semantic_scholar": {
    "enabled": true,
    "rate_limit_seconds": 1,
    "api_key_env": "SEMANTIC_SCHOLAR_API_KEY"
  }
}
```

**Adjust based on API tier:**
- Free tier: Use conservative limits (3-5 seconds)
- Paid tier: Can reduce to 0.5-1 second

### 3. Quality Threshold Optimization

Edit `config/quality_config.yaml`:

```yaml
quality_filter:
  enabled: true

  # Adjust based on desired precision/recall
  citation_thresholds:
    "0-1": 3   # Increase to 5 for higher precision
    "1-2": 10  # Increase to 15 for higher precision
    "2-5": 20
    "5+": 30
```

Edit `config/heuristics.json`:

```json
{
  "sensitivity": "high",
  "thresholds": {
    "value_score_minimum": 6.0,  // Increase to 7.0 for higher precision
    "confidence_minimum": 5.0,   // Increase to 6.0 to require higher confidence
    "tier_s_threshold": 9.0,
    "tier_a_threshold": 7.5,
    "tier_b_threshold": 6.0
  }
}
```

### 4. Cost Management and Monitoring

**Estimate API Costs:**

```python
# Average cost per paper evaluation
cost_per_evaluation = 0.0025  # $0.0025 for Haiku

# Batch mode (30 days, ~500 papers)
estimated_papers = 500
estimated_cost = estimated_papers * cost_per_evaluation
# ~$1.25 per batch run

# Monitor mode (daily, ~50 new papers/day)
daily_papers = 50
monthly_cost = daily_papers * 30 * cost_per_evaluation
# ~$3.75 per month
```

**Set API Budget Alerts:**

```bash
# Claude console > Settings > Billing > Budget Alerts
# Set alert at $10/month for safety
```

**Track Costs:**

```bash
# Add to monitoring dashboard
grep "AI evaluation" logs/analyzer.log | wc -l  # Count evaluations
```

---

## Scaling Considerations

### 1. Parallel Processing

**Run Multiple Workers:**

```bash
# Terminal 1: arXiv only
docker compose -f docker-compose-arxiv.yml up -d

# Terminal 2: Semantic Scholar only
docker compose -f docker-compose-scholar.yml up -d
```

**docker-compose-arxiv.yml:**
```yaml
services:
  analyzer-arxiv:
    build: ..
    environment:
      - SOURCES_FILTER=arxiv
    volumes:
      - ../findings:/app/findings
```

### 2. Database Backend for Findings

**PostgreSQL Integration (Future Enhancement):**

```python
# models/opportunity.py
def save_to_db(self, db_connection):
    """Save assessment to PostgreSQL instead of files."""
    cursor = db_connection.cursor()
    cursor.execute(
        """
        INSERT INTO opportunities (
            id, paper_id, data_type_name, value_score,
            confidence_score, tier, detected_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        (self.id, self.paper.id, self.data_type_name,
         self.value_score, self.confidence_score,
         self.tier, self.detected_at)
    )
    db_connection.commit()
```

### 3. Distributed Scraping

**Celery Task Queue (Future Enhancement):**

```python
# tasks.py
from celery import Celery

app = Celery('analyzer', broker='redis://localhost:6379/0')

@app.task
def analyze_paper(paper_id):
    """Process single paper asynchronously."""
    # Fetch paper
    # Extract signals
    # Evaluate with AI
    # Save results
```

### 4. Load Balancing

**NGINX Config:**

```nginx
upstream analyzer {
    server analyzer1:8000;
    server analyzer2:8000;
    server analyzer3:8000;
}

server {
    listen 80;
    location / {
        proxy_pass http://analyzer;
    }
}
```

---

## Monitoring and Observability

### 1. Log Analysis

**Structured Logging:**

```bash
# View findings summary
grep "✓ Tier" logs/analyzer.log

# Count by tier
grep "✓ Tier A" logs/analyzer.log | wc -l
grep "✓ Tier B" logs/analyzer.log | wc -l

# View errors
grep "ERROR" logs/analyzer.log

# View API rate limits
grep "rate limit" logs/analyzer.log
```

**Log Rotation:**

```bash
# /etc/logrotate.d/research-analyzer
/path/to/ai_working/research_data_analyzer/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0640 youruser yourgroup
}
```

### 2. Error Tracking

**Sentry Integration (Optional):**

```python
# main.py
import sentry_sdk

sentry_sdk.init(
    dsn="https://your-dsn@sentry.io/project-id",
    traces_sample_rate=0.1
)
```

### 3. Performance Metrics

**Key Metrics to Track:**

```bash
# Papers processed per hour
grep "Processing paper" logs/analyzer.log | \
  awk '{print $1" "$2}' | uniq -c

# Average evaluation time
grep "Evaluation time" logs/analyzer.log | \
  awk '{sum+=$NF; count++} END {print sum/count}'

# Success rate
total=$(grep "Processing paper" logs/analyzer.log | wc -l)
success=$(grep "✓ Tier" logs/analyzer.log | wc -l)
echo "Success rate: $(($success * 100 / $total))%"
```

**Prometheus Metrics (Future Enhancement):**

```python
from prometheus_client import Counter, Histogram

papers_processed = Counter('papers_processed_total', 'Total papers processed')
evaluation_duration = Histogram('evaluation_duration_seconds', 'AI evaluation duration')
```

### 4. Cost Tracking

**Daily Cost Report:**

```bash
#!/bin/bash
# cost-report.sh

DATE=$(date +%Y-%m-%d)
EVALUATIONS=$(grep "AI evaluation" logs/analyzer-$DATE.log | wc -l)
COST=$(echo "$EVALUATIONS * 0.0025" | bc -l)

echo "Date: $DATE"
echo "Evaluations: $EVALUATIONS"
echo "Estimated Cost: \$$COST"
```

### 5. Alert Configuration

**Healthchecks.io Integration:**

```bash
#!/bin/bash
# healthcheck.sh

# Run batch analysis
python -m research_data_analyzer.main --mode batch --lookback-days 1

# Ping success
if [ $? -eq 0 ]; then
    curl -fsS --retry 3 https://hc-ping.com/your-uuid
else
    curl -fsS --retry 3 https://hc-ping.com/your-uuid/fail
fi
```

**Uptime Robot Setup:**
```
Monitor Type: Keyword Monitor
URL: http://your-server/health
Keyword: "status: healthy"
Alert Contacts: your@email.com
```

---

## Troubleshooting

### Common Issues

#### 1. Container Exits Immediately

**Symptoms:**
```bash
docker compose up -d analyzer
# Container stops after 1-2 seconds
```

**Diagnosis:**
```bash
docker compose logs analyzer
```

**Solutions:**

**Missing API Key:**
```bash
# Check .env file
cat .env | grep ANTHROPIC_API_KEY

# Verify it's loaded in container
docker exec research_data_analyzer env | grep ANTHROPIC
```

**Invalid API Key:**
```bash
# Test API key
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01"
```

**Port Conflict:**
```bash
# Check if port is in use
docker ps | grep 8000

# Change port in docker-compose.yml
```

#### 2. No Findings Generated

**Symptoms:**
- Analyzer runs successfully
- No files in `findings/` directory

**Diagnosis:**
```bash
# Check if papers are being scraped
grep "Found.*papers from" logs/analyzer.log

# Check if any pass quality filter
grep "Quality Filter Results" logs/analyzer.log

# Check threshold settings
cat config/heuristics.json | grep value_score_minimum
```

**Solutions:**

**Thresholds Too High:**
```json
// config/heuristics.json
{
  "thresholds": {
    "value_score_minimum": 5.0  // Lower from 6.0
  }
}
```

**No New Papers:**
```bash
# Increase lookback period
python -m research_data_analyzer.main --mode batch --lookback-days 180
```

**API Rate Limits:**
```bash
# Check logs for rate limit errors
grep "rate limit" logs/analyzer.log

# Increase delays in config/sources.json
```

**Sources Disabled:**
```json
// config/sources.json
{
  "arxiv": {
    "enabled": true  // Ensure true
  }
}
```

#### 3. High API Usage/Costs

**Symptoms:**
- Anthropic bills higher than expected
- Rate limit errors

**Diagnosis:**
```bash
# Count evaluations
grep "AI evaluation" logs/analyzer.log | wc -l

# Calculate estimated cost
# evaluations * $0.0025 = total cost
```

**Solutions:**

**Increase Quality Thresholds:**
```json
// config/heuristics.json
{
  "thresholds": {
    "value_score_minimum": 8.0  // Higher = fewer AI evaluations
  }
}
```

**Disable Sources:**
```json
// config/sources.json
{
  "papers_with_code": {
    "enabled": false  // Disable if not needed
  }
}
```

**Increase Poll Interval:**
```env
# .env
POLL_INTERVAL_HOURS=48  // Check less frequently
```

**Reduce Lookback:**
```env
# .env
LOOKBACK_DAYS=30  // Scan fewer papers
```

#### 4. Slow Performance

**Symptoms:**
- Processing takes hours
- High CPU/memory usage

**Diagnosis:**
```bash
# Monitor resource usage
docker stats research_data_analyzer

# Check rate limiting delays
grep "rate limit" logs/analyzer.log

# Identify bottlenecks
grep "Evaluation time" logs/analyzer.log | sort -n
```

**Solutions:**

**Reduce Rate Limit Delays:**
```json
// config/sources.json - only if you have API keys
{
  "arxiv": {
    "rate_limit_seconds": 1  // Reduce from 3
  }
}
```

**Increase Docker Resources:**
```yaml
# docker-compose.yml
services:
  analyzer:
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 8G
```

**Parallelize Scraping:**
```bash
# Run separate instances for each source
docker compose -f docker-compose-arxiv.yml up -d
docker compose -f docker-compose-scholar.yml up -d
```

#### 5. Debug Mode

**Enable detailed logging:**

```bash
# Local
python -m research_data_analyzer.main --mode batch --log-level DEBUG

# Docker
docker compose run -e LOG_LEVEL=DEBUG analyzer-batch
```

**Python debugger:**

```python
# Add to code for breakpoint
import pdb; pdb.set_trace()

# Run with debug mode
python -m pdb -m research_data_analyzer.main --mode batch
```

#### 6. Recovery Procedures

**Restart from Checkpoint:**
```bash
# Session state is in .sessions/
ls -la .sessions/

# Delete to force fresh start
rm -rf .sessions/*

# Container will create new session on next run
docker compose restart analyzer
```

**Recover Lost Findings:**
```bash
# Findings are timestamped, look for recent
find findings/ -type f -mtime -1

# Restore from backup
tar -xzf backups/findings-20250101.tar.gz
```

---

## Backup and Disaster Recovery

### 1. Findings Backup Strategy

**Automated Daily Backups:**

```bash
#!/bin/bash
# backup-findings.sh

DATE=$(date +%Y%m%d)
BACKUP_DIR="/backups/research-analyzer"
SOURCE_DIR="/path/to/ai_working/research_data_analyzer"

mkdir -p $BACKUP_DIR

# Backup findings
tar -czf $BACKUP_DIR/findings-$DATE.tar.gz \
    $SOURCE_DIR/findings/

# Backup sessions
tar -czf $BACKUP_DIR/sessions-$DATE.tar.gz \
    $SOURCE_DIR/.sessions/

# Backup configuration
tar -czf $BACKUP_DIR/config-$DATE.tar.gz \
    $SOURCE_DIR/config/

# Keep last 30 days
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete

# Upload to cloud storage (optional)
aws s3 sync $BACKUP_DIR s3://your-bucket/research-analyzer-backups/

echo "✓ Backup completed: $DATE"
```

**Add to crontab:**
```bash
# Run daily at 2 AM
0 2 * * * /path/to/backup-findings.sh >> /var/log/research-analyzer-backup.log 2>&1
```

### 2. State Preservation

**Session State:**
```bash
# Sessions track scraping progress
ls .sessions/
# arxiv_session.json
# semantic_scholar_session.json

# Backup before major changes
cp -r .sessions .sessions.backup
```

**Configuration Version Control:**
```bash
# Track config changes with git
cd config/
git init
git add .
git commit -m "Initial configuration"

# Before making changes
git commit -am "Update: increase citation thresholds"
```

### 3. Recovery Procedures

**Restore from Backup:**

```bash
# Stop running instances
docker compose down

# Restore findings
tar -xzf backups/findings-20250101.tar.gz -C /path/to/

# Restore sessions
tar -xzf backups/sessions-20250101.tar.gz -C /path/to/

# Restart
docker compose up -d analyzer
```

**Partial Recovery (Single Tier):**

```bash
# Restore only Tier A findings
tar -xzf backups/findings-20250101.tar.gz \
    --wildcards 'findings/tier_A/*'
```

**Configuration Rollback:**

```bash
cd config/
git log --oneline  # View history
git checkout abc123  # Restore to specific version
```

### 4. Disaster Recovery Plan

**Total System Loss:**

1. **Restore from Cloud Backup:**
   ```bash
   aws s3 sync s3://your-bucket/research-analyzer-backups/ ./backups/
   ```

2. **Rebuild Environment:**
   ```bash
   cd ai_working/research_data_analyzer
   cp .env.backup .env
   docker compose build
   ```

3. **Restore Data:**
   ```bash
   tar -xzf backups/findings-latest.tar.gz
   tar -xzf backups/sessions-latest.tar.gz
   ```

4. **Verify and Restart:**
   ```bash
   docker compose up -d analyzer
   docker compose logs -f analyzer
   ```

**RTO (Recovery Time Objective):** < 1 hour
**RPO (Recovery Point Objective):** < 24 hours (daily backups)

---

## Cross-References

- **docker/README.md**: Docker-specific deployment details
- **README.md**: General usage and quick start
- **docs/QUALITY_VALIDATION.md**: Quality system configuration
- **config/**: All configuration files

---

## Production Checklist

Before deploying to production:

- [ ] API keys stored in secrets manager (not .env)
- [ ] Rate limiting configured for API tier
- [ ] Quality thresholds tuned for precision/recall
- [ ] Logging configured with rotation
- [ ] Monitoring dashboard set up
- [ ] Alerts configured for failures
- [ ] Backup script automated and tested
- [ ] Recovery procedure documented and tested
- [ ] Resource limits set in Docker
- [ ] Cost tracking enabled
- [ ] Health check endpoint working
- [ ] SSL/TLS configured (if applicable)

---

## Support

For deployment issues:
1. Check logs: `docker compose logs analyzer`
2. Review this guide's troubleshooting section
3. Verify configuration files
4. Test API keys with curl
5. Check network connectivity to APIs

**Common Issues Summary:**
- Missing API key → Check .env file
- No findings → Lower thresholds or increase lookback
- High costs → Increase thresholds or reduce polling
- Slow performance → Check rate limits and resources
