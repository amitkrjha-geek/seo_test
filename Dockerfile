# ─────────────────────────────────────────────
# Stage 1: Build React frontend
# ─────────────────────────────────────────────
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ .
RUN npm run build
# Output: /app/frontend/dist

# ─────────────────────────────────────────────
# Stage 2: Python backend + serve frontend
# ─────────────────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

# System deps for lxml / other C extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libxml2-dev \
    libxslt-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/pyproject.toml ./
RUN pip install --no-cache-dir .

# Install spaCy English model
RUN python -m spacy download en_core_web_sm

# Copy backend source
COPY backend/ .

# Copy built frontend into backend/static so FastAPI can serve it
COPY --from=frontend-builder /app/frontend/dist ./static

# Persistent SQLite data directory
RUN mkdir -p data

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
