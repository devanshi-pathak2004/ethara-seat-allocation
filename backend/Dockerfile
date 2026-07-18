FROM python:3.12-slim

WORKDIR /app

# Install dependencies first (better layer caching).
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code.
COPY . .

# Seed the database on first build if none exists, then serve.
ENV PYTHONUNBUFFERED=1
EXPOSE 8000

# On container start: create tables + seed if empty, then run the API.
CMD ["sh", "-c", "python -m app.seed_if_empty && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
