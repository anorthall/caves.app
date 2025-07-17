# syntax=docker/dockerfile:1.7-labs
FROM python:3.13-slim
COPY --from=ghcr.io/astral-sh/uv:0.7.21 /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE="1"
ENV UV_FROZEN="1"
ENV UV_LINK_MODE="copy"
ENV UV_PROJECT_ENVIRONMENT="/app/.venv"
ENV VIRTUAL_ENV="${UV_PROJECT_ENVIRONMENT}"
ENV PYTHONPATH="/app/:/app/app/"
ENV PATH="/app/.venv/bin:${PATH}"
ENV TINI_SUBREAPER="1"
ENV DJANGO_SETTINGS_MODULE="conf.settings.production"

RUN groupadd app && useradd -g app -m -d /app app && \
    mkdir -p /app /app/staticfiles /app/mediafiles && \
    apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    postgresql-client \
    netcat-traditional \
    libmagic-dev \
    libproj-dev \
    libgeos-dev \
    gdal-bin \
    tini && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app/

COPY --chown=app:app uv.lock pyproject.toml /app/

RUN uv sync --frozen

COPY --chown=app:app \
     --exclude=./.* \
     --exclude=*.MD \
     --exclude=**.env \
     --exclude=./data \
     --exclude=./frontend \
     . .

RUN python /app/app/manage.py collectstatic --noinput && \
    chmod +x /app/conf/run.sh

USER app
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["/app/conf/run.sh", "start"]
