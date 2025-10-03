# NL2MySQL Dockerfile - Groq-Only Setup
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive
# Groq-optimized settings
ENV LLM_PROVIDER=groq
ENV REQUESTS_TIMEOUT=30

# Install system dependencies for MySQL
RUN apt-get update && apt-get install -y \
    curl \
    default-libmysqlclient-dev \
    pkg-config \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies (optimized for Groq-only setup)
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && pip cache purge

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p chromadb logs

# Set permissions for essential scripts
RUN chmod +x schema_inspector.py schema_embedder.py app.py

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]

# Alternative commands (can be overridden):
# For schema extraction:
# CMD ["python", "schema_inspector.py"]
# 
# For schema embedding:
# CMD ["python", "schema_embedder.py", "--reset"]
#
# For development with reload:
# CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
#
# For production with Groq:
# Ensure GROQ_API_KEY environment variable is set
