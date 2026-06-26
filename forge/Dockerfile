FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for tree-sitter
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install poetry
RUN pip install --no-cache-dir poetry

# Copy dependency files first for layer caching
COPY backend/pyproject.toml backend/poetry.lock* ./

# Install dependencies (no dev)
RUN poetry config virtualenvs.create false \
    && poetry install --no-dev --no-interaction --no-ansi

# Copy application code
COPY backend/src/ ./src/

# Set Python path
ENV PYTHONPATH=/app/src

EXPOSE 8000

CMD ["uvicorn", "forge.presentation.app:app", "--host", "0.0.0.0", "--port", "8000"]