# ============================================================================
# DJANGO RESTFUL LOGISTICS TEMPLATE - PRODUCTION DOCKERFILE
# ============================================================================
# Multi-stage build for optimized production image

# ============================================================================
# STAGE 1: Build dependencies
# ============================================================================
FROM python:3.11-slim as builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gcc \
    g++ \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r requirements.txt

# ============================================================================
# STAGE 2: Production image
# ============================================================================
FROM python:3.11-slim as production

# Build arguments
ARG BUILD_ENV=production
ARG APP_USER=django
ARG APP_GROUP=django
ARG APP_UID=1000
ARG APP_GID=1000

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV DJANGO_SETTINGS_MODULE=config.settings.${BUILD_ENV}
ENV PATH="/opt/venv/bin:$PATH"

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    curl \
    wget \
    gettext \
    mime-support \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Create app user and group
RUN groupadd -g ${APP_GID} ${APP_GROUP} \
    && useradd -u ${APP_UID} -g ${APP_GID} -m -s /bin/bash ${APP_USER}

# Set work directory
WORKDIR /app

# Create necessary directories
RUN mkdir -p \
    /app/staticfiles \
    /app/media \
    /app/logs \
    /app/backups \
    /app/tmp \
    && chown -R ${APP_USER}:${APP_GROUP} /app

# Copy application code
COPY --chown=${APP_USER}:${APP_GROUP} . /app/

# Copy entrypoint script
COPY --chown=${APP_USER}:${APP_GROUP} scripts/docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Switch to non-root user
USER ${APP_USER}

# Expose ports
EXPOSE 8000 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/api/health/ || exit 1

# Set entrypoint
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]

# Default command
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
