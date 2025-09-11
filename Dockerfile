FROM python:3.10-slim

# Set environment variables
ENV JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install Java for PySpark
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        openjdk-21-jre-headless \
    && apt-get autoremove -yqq --purge \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy Pipfile first (for better layer caching)
COPY Pipfile Pipfile.lock ./

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip pipenv \
    && pipenv install --deploy --system --ignore-pipfile \
    && pip cache purge

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser \
    && chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Ensure logs directory exists with proper permissions
RUN mkdir -p /app/app/logs
