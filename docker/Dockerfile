FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for dependency management
RUN pip install uv

# Copy project files
COPY pyproject.toml* uv.lock* ./
COPY ai_working/research_data_analyzer/ ./research_data_analyzer/
COPY amplifier/ccsdk_toolkit/ ./amplifier/ccsdk_toolkit/ 2>/dev/null || true

# Install dependencies (if pyproject.toml exists)
RUN if [ -f pyproject.toml ]; then uv sync; fi || echo "No pyproject.toml found, skipping uv sync"

# If no pyproject.toml, install manually
RUN if [ ! -f pyproject.toml ]; then \
    pip install anthropic httpx python-dotenv; \
    fi

# Create directories
RUN mkdir -p /app/findings /app/.sessions /app/config

# Copy default configs
COPY ai_working/research_data_analyzer/config/*.json /app/config/

# Set environment variables
ENV PYTHONPATH=/app
ENV FINDINGS_DIR=/app/findings

# Entry point
CMD ["python", "-m", "research_data_analyzer.main"]
