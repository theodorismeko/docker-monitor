# Use the smallest Python image
FROM python:3.11-alpine

# Set working directory
WORKDIR /app

# Install only essential system dependencies
RUN apk add --no-cache \
    curl \
    && rm -rf /var/cache/apk/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies with optimizations
RUN pip install --no-cache-dir --no-compile -r requirements.txt \
    && pip cache purge

# Add build argument to bust cache for code copying
ARG BUILD_DATE
ENV BUILD_DATE=${BUILD_DATE}

# Create a timestamp file to bust cache (this will change with each build)
RUN echo "Build timestamp: ${BUILD_DATE}" > /tmp/build_timestamp

# Copy application code (this layer will be rebuilt when BUILD_DATE changes)
COPY docker_monitor/ ./docker_monitor/
COPY scripts/ ./scripts/
COPY config/ ./config/

# Create logs directory
RUN mkdir -p /app/logs

# Set environment variables for optimization
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1 
ENV PYTHONOPTIMIZE=2


# Default command - run scheduled monitoring
CMD ["python3", "scripts/run_monitor.py", "--scheduled"]