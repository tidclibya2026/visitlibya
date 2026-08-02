FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PORT=8000

WORKDIR /app

RUN groupadd --system visitlibya \
    && useradd --system --gid visitlibya --home-dir /app visitlibya

COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=visitlibya:visitlibya app ./app
COPY --chown=visitlibya:visitlibya alembic ./alembic
COPY --chown=visitlibya:visitlibya scripts ./scripts
COPY --chown=visitlibya:visitlibya alembic.ini ./alembic.ini

USER visitlibya
EXPOSE 8000

CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers ${WEB_CONCURRENCY:-1} --proxy-headers --forwarded-allow-ips ${FORWARDED_ALLOW_IPS:-127.0.0.1}"]
