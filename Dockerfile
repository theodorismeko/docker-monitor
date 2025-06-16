FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

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

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Default command - run scheduled monitoring
CMD ["python3", "scripts/run_monitor.py", "--scheduled"] 