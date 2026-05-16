# ── Build stage ───────────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Runtime stage ──────────────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

LABEL maintainer="AI Code Reviewer <dev@aicodereviewer.io>"
LABEL description="AI-powered CLI code reviewer"
LABEL version="1.0.0"

# Git is needed at runtime for diff reading
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Create non-root user
RUN useradd --create-home --shell /bin/bash reviewer
USER reviewer
WORKDIR /workspace

# Copy application source
COPY --chown=reviewer:reviewer . /app
RUN pip install --no-cache-dir -e /app --user

# Make sure user scripts are in PATH
ENV PATH="/home/reviewer/.local/bin:$PATH"

# Default entrypoint
ENTRYPOINT ["aicodereviewer"]
CMD ["--help"]
