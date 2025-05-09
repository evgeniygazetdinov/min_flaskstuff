FROM python:3.10-slim as builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
FROM python:3.10-slim
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.10/site-packages/ /usr/local/lib/python3.10/site-packages/
COPY ./main.py ./models.py ./etcd_client.py ./


ENV PYTHONUNBUFFERED=1
ENV ETCD_HOST=localhost
ENV ETCD_PORT=2379

HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/docs || exit 1
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]