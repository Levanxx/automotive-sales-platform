FROM python:3.12-slim
WORKDIR /app
COPY shared ./shared
COPY services ./services
COPY scripts ./scripts
ENV PYTHONUNBUFFERED=1 PYTHONPATH=/app
CMD ["python", "-m", "services.prospects.app"]
