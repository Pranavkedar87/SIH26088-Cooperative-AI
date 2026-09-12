# ═══════════════════════════════════════════════════════════════════════
# SahkaarSetu (SIH26088) — Production Backend Dockerfile
# Multi-lingual Cooperative Governance & Legal Assistance FastAPI Backend
# ═══════════════════════════════════════════════════════════════════════

FROM python:3.11-slim

# Prevent Python from writing .pyc files and buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000 \
    APP_ENV=production \
    LOG_LEVEL=INFO \
    AI_PROVIDER=ollama \
    OLLAMA_BASE_URL=http://localhost:11434 \
    OLLAMA_MODEL=qwen3:8b \
    EMBEDDING_PROVIDER=local \
    LOCAL_EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-mpnet-base-v2

WORKDIR /app

# Install system utilities needed for networking and SSL
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Pre-download local FastEmbed multilingual model into image cache for instant cold starts
RUN python -c "from fastembed import TextEmbedding; TextEmbedding(model_name='sentence-transformers/paraphrase-multilingual-mpnet-base-v2')"

# Copy application source code
COPY . .

# Expose container port
EXPOSE 8000

# Health check against lightweight /health endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Start Uvicorn bound to 0.0.0.0 and platform-provided $PORT
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT}
