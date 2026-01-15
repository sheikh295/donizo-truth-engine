# Donizo Truth Engine - Interactive Docker Image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY requirements.txt setup.py ./
COPY donizo_engine/ ./donizo_engine/
COPY docs/donizo_truth_engine_prd.md ./

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -e .

# Copy application files
COPY generate_test_data.py ./
COPY interactive_menu.py ./
COPY tests/ ./tests/

# Make interactive menu executable
RUN chmod +x interactive_menu.py

# Create directory for data files
RUN mkdir -p /data

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV TERM=xterm-256color

# Default command: Interactive menu
CMD ["python3", "/app/interactive_menu.py"]
