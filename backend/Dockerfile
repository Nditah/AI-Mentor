FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FORWARDED_ALLOW_IPS=127.0.0.1

WORKDIR /app
RUN useradd --create-home --uid 10001 mentor
COPY pyproject.toml alembic.ini ./
COPY app ./app
COPY alembic ./alembic
RUN pip install --no-cache-dir .
USER mentor
EXPOSE 8000
# Migrations run as a separate job: `python -m app.cli migrate` (Deployment.md).
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips \"$FORWARDED_ALLOW_IPS\""]
