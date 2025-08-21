FROM python:3.11-slim AS builder

WORKDIR /app
    
# Install Poetry
RUN pip install --no-cache-dir poetry

# Copy project files
COPY pyproject.toml poetry.lock ./
COPY README.md ./         

# Install dependencies in isolated environment
RUN poetry config virtualenvs.create false \
    && poetry install --without dev --no-interaction --no-ansi --no-root

# Copy project files
COPY . .


FROM python:3.11-slim

WORKDIR /app
RUN pip install --no-cache-dir uvicorn
# Copy from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /app /app

# Expose port
EXPOSE 8000

# Start Uvicorn
CMD ["uvicorn", "weather_analytics_api.api:app", "--host", "0.0.0.0", "--port", "8000"]
    