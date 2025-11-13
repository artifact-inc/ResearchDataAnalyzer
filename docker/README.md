# Docker Deployment Guide

## Quick Start

### 1. Setup Environment

```bash
# Navigate to project directory
cd ai_working/research_data_analyzer

# Copy .env template
cp .env.example .env

# Edit .env and add your API keys
nano .env  # or use your preferred editor
```

### 2. Run Batch Analysis (One-Time Scan)

```bash
cd docker
docker-compose --profile batch up analyzer-batch
```

This will:
- Scan papers from the past 90 days (configurable via `LOOKBACK_DAYS`)
- Save findings to `../findings/`
- Exit when complete

### 3. Run Continuous Monitoring (Background Service)

```bash
cd docker
docker-compose up -d analyzer
```

This will:
- Start monitoring service in background
- Check for new papers every 24 hours (configurable via `POLL_INTERVAL_HOURS`)
- Keep running until stopped

### 4. View Logs

```bash
# Follow logs in real-time
docker-compose logs -f analyzer

# View last 100 lines
docker-compose logs --tail=100 analyzer
```

### 5. Stop Monitoring

```bash
docker-compose down
```

---

## Configuration

### Environment Variables (.env file)

```env
# Required: Anthropic API Key
ANTHROPIC_API_KEY=your_key_here

# Optional: Semantic Scholar API Key (for higher rate limits)
SEMANTIC_SCHOLAR_API_KEY=your_key_here

# Operating mode (batch or monitor)
MODE=monitor

# Monitoring interval in hours (minimum 1)
POLL_INTERVAL_HOURS=24

# Initial lookback period in days
LOOKBACK_DAYS=90

# Log level (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO
```

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
    "enabled": true,  // Set to false to disable
    ...
  },
  "papers_with_code": {
    "enabled": true,
    ...
  }
}
```

---

## Volume Mounts

The Docker container uses these volume mounts:

| Host Path | Container Path | Purpose |
|-----------|---------------|---------|
| `../findings` | `/app/findings` | Output directory (findings organized by tier) |
| `../config` | `/app/config` | Configuration files (read-only) |
| `../.sessions` | `/app/.sessions` | Session persistence (checkpoints) |
| `../.env` | `/app/.env` | Environment variables (read-only) |

---

## Troubleshooting

### Problem: Container exits immediately

**Solution**: Check logs for errors
```bash
docker-compose logs analyzer
```

Common issues:
- Missing `ANTHROPIC_API_KEY` in `.env`
- Invalid API key
- Port conflicts (if running multiple instances)

### Problem: No findings generated

**Possible causes**:
1. **Thresholds too high**: Lower `value_score_minimum` in `config/heuristics.json`
2. **No new papers**: Check date range with `LOOKBACK_DAYS`
3. **API rate limits**: Check logs for rate limit errors
4. **Source disabled**: Ensure sources are enabled in `config/sources.json`

### Problem: High API usage/costs

**Solutions**:
1. Increase rate limits in `config/sources.json`
2. Disable sources you don't need
3. Increase `POLL_INTERVAL_HOURS` for continuous mode
4. Reduce `LOOKBACK_DAYS` for batch mode

---

## Advanced Usage

### Custom Docker Compose Commands

```bash
# Run with custom lookback period (7 days)
LOOKBACK_DAYS=7 docker-compose --profile batch up analyzer-batch

# Run monitoring with hourly checks
POLL_INTERVAL_HOURS=1 docker-compose up -d analyzer

# Rebuild after code changes
docker-compose build --no-cache

# View resource usage
docker stats research_data_analyzer
```

### Manually Enter Container

```bash
# Start interactive shell in running container
docker exec -it research_data_analyzer /bin/bash

# Run Python REPL
docker exec -it research_data_analyzer python

# Run batch mode manually with custom args
docker exec -it research_data_analyzer python -m research_data_analyzer.main --mode batch --lookback-days 7
```

### Clean Up Old Data

```bash
# Stop container
docker-compose down

# Remove old findings (be careful!)
rm -rf ../findings/tier_*

# Remove sessions (forces fresh start)
rm -rf ../.sessions/*

# Start fresh
docker-compose up -d analyzer
```

---

## Production Deployment

### Deploy to Cloud VM (AWS, DigitalOcean, etc.)

```bash
# 1. SSH into server
ssh user@your-server.com

# 2. Install Docker and Docker Compose
curl -fsSL https://get.docker.com | sh
sudo apt-get install docker-compose-plugin

# 3. Clone repository or copy files
git clone your-repo.git
cd your-repo/ai_working/research_data_analyzer

# 4. Setup .env file
cp .env.example .env
nano .env  # Add API keys

# 5. Start monitoring service
cd docker
docker-compose up -d analyzer

# 6. Setup log rotation (optional)
cat > /etc/logrotate.d/research-analyzer <<EOF
/var/lib/docker/containers/*/*.log {
  rotate 7
  daily
  compress
  delaycompress
  missingok
  notifempty
}
EOF
```

### Setup Automated Backups

```bash
#!/bin/bash
# backup-findings.sh

DATE=$(date +%Y%m%d)
BACKUP_DIR="/backups/research-analyzer"

mkdir -p $BACKUP_DIR

# Backup findings
tar -czf $BACKUP_DIR/findings-$DATE.tar.gz \
    /path/to/ai_working/research_data_analyzer/findings/

# Backup sessions
tar -czf $BACKUP_DIR/sessions-$DATE.tar.gz \
    /path/to/ai_working/research_data_analyzer/.sessions/

# Keep last 30 days
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete

echo "Backup completed: $DATE"
```

Add to crontab:
```bash
# Run daily at 2 AM
0 2 * * * /path/to/backup-findings.sh
```

---

## Monitoring & Alerting

### Check Container Health

```bash
#!/bin/bash
# check-health.sh

CONTAINER="research_data_analyzer"

if [ "$(docker ps -q -f name=$CONTAINER)" ]; then
    echo "✅ Container is running"

    # Check if finding recent findings
    RECENT_FINDINGS=$(find ../findings -type f -mmin -60 | wc -l)
    if [ $RECENT_FINDINGS -gt 0 ]; then
        echo "✅ Found $RECENT_FINDINGS new findings in last hour"
    else
        echo "⚠️  No new findings in last hour (may be normal)"
    fi
else
    echo "❌ Container is not running!"
    exit 1
fi
```

### Setup Email Alerts (Optional)

Integrate with monitoring services:
- **Uptime Robot**: Monitor container health endpoint
- **Healthchecks.io**: Ping after successful runs
- **PagerDuty**: Alert on failures

---

## Performance Tuning

### Optimize for Speed

```json
// config/sources.json
{
  "arxiv": {
    "rate_limit_seconds": 1  // Faster, but respect arXiv limits
  }
}
```

### Optimize for Cost (Lower API Usage)

```json
// config/heuristics.json
{
  "thresholds": {
    "value_score_minimum": 8.0  // Higher threshold = fewer AI evaluations
  }
}
```

---

## Scaling

### Multiple Instances

To run multiple analyzers in parallel (e.g., different sources):

```yaml
# docker-compose-multi.yml
version: '3.8'

services:
  analyzer-arxiv:
    build: ...
    environment:
      - SOURCES_FILTER=arxiv
    ...

  analyzer-pwc:
    build: ...
    environment:
      - SOURCES_FILTER=papers_with_code
    ...
```

### Database Backend (Future Enhancement)

For large-scale deployments, consider:
- PostgreSQL for findings storage
- Redis for caching
- Elasticsearch for full-text search

---

## Maintenance

### Update Code

```bash
# Pull latest changes
git pull

# Rebuild container
cd docker
docker-compose down
docker-compose build --no-cache
docker-compose up -d analyzer
```

### Monitor Disk Usage

```bash
# Check findings directory size
du -sh ../findings

# Check Docker disk usage
docker system df
```

### Regular Cleanup

```bash
# Remove old Docker images
docker image prune -a

# Remove unused volumes
docker volume prune
```

---

## Support

For issues or questions:
1. Check logs: `docker-compose logs analyzer`
2. Review configuration files
3. Ensure API keys are valid
4. Check network connectivity
5. Consult main README.md for detailed documentation
