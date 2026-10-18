FROM python:3.11-slim as builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt requirements.txt
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.11-slim

WORKDIR /app

COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Initialize data directories
RUN mkdir -p /app/data/indices/faiss /app/data/indices/bm25 /app/data/raw/papers /app/data/benchmarks/results

COPY backend/app /app/backend/app
COPY data /app/data
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

EXPOSE 8000

# Support dynamic Render $PORT or default 8000
CMD ["sh", "-c", "uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
