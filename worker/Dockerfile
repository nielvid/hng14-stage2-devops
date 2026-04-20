# syntax=docker/dockerfile:1
FROM python:3.12-alpine AS builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.12-alpine
WORKDIR /app
COPY --from=builder /install /usr/local
COPY worker.py .

RUN adduser -D -u 1001 appuser
USER appuser

HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import redis, os; r=redis.Redis(host=os.getenv('REDIS_HOST','redis')); r.ping()"

CMD ["python", "worker.py"]
