# Multi-stage build for tg_analyzer

# Stage 1: Build stage
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime stage
FROM python:3.11-slim

WORKDIR /app

# Create non-root user
RUN useradd -m -u 1000 analyzer && \
    chown -R analyzer:analyzer /app

# Copy installed packages from builder
COPY --from=builder /root/.local /home/analyzer/.local

# Update PATH
ENV PATH=/home/analyzer/.local/bin:$PATH

# Copy application code
COPY --chown=analyzer:analyzer src/ ./src/
COPY --chown=analyzer:analyzer config/ ./config/

# Create output directory
RUN mkdir -p /app/output && chown analyzer:analyzer /app/output

# Switch to non-root user
USER analyzer

# Set Python to run in unbuffered mode
ENV PYTHONUNBUFFERED=1

# Entry point
ENTRYPOINT ["python", "-m", "src.cli.analyze"]
CMD ["--help"]
