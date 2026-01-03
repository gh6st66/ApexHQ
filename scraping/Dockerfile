FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml /app/pyproject.toml
COPY src /app/src
COPY config /app/config

RUN pip install --no-cache-dir .

ENV PYTHONUNBUFFERED=1
ENV APEXHQ_SOURCES_FILE=/app/config/sources.json

CMD ["python", "-m", "apexhq_scraper"]
