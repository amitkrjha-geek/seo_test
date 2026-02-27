FROM python:3.11-slim

WORKDIR /app

# Install system dependencies required by lxml, playwright, etc.
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libxml2-dev \
    libxslt-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency definition and install
COPY pyproject.toml .
RUN pip install --no-cache-dir .

# Install spaCy model (used for NLP)
RUN python -m spacy download en_core_web_sm

# Copy application code
COPY . .

# Create the data directory for SQLite
RUN mkdir -p data

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
