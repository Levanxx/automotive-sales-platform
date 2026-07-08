FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY shared ./shared
COPY services ./services
COPY scripts ./scripts
COPY load-tests ./load-tests
ENV PYTHONUNBUFFERED=1 PYTHONPATH=/app
CMD ["python", "-m", "services.prospects.app"]
