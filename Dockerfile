# syntax=docker/dockerfile:1.7

FROM python:3.14.6-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install system dependencies only if needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first for better Docker layer caching
COPY requirements.txt .

RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# Copy source code after dependencies
COPY . .

# Create non-root user
RUN useradd -m appuser
USER appuser

CMD ["python", "main.py"]
