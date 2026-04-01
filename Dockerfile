# Multi-stage Dockerfile for Autonomous GitHub Agent
# Optimized for size and security

# Stage 1: Builder
FROM python:3.11-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim

WORKDIR /app

# Create non-root user for security
RUN useradd -m -u 1000 agent && chown -R agent:agent /app

# Copy Python packages from builder
COPY --from=builder /root/.local /home/agent/.local

# Copy application code
COPY --chown=agent:agent .github/ ./.github/
COPY --chown=agent:agent *.py ./
COPY --chown=agent:agent *.yml *.yaml ./

# Set PATH for user packages
ENV PATH=/home/agent/.local/bin:$PATH

# Switch to non-root user
USER agent

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Default command
CMD ["python", ".github/scripts/ai_agent_main.py", "--context", "context.json"]  
