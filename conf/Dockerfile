# syntax=docker/dockerfile:1
FROM python:3.13-slim
COPY --from=ghcr.io/astral-sh/uv:0.6.0 /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1
ENV UV_FROZEN=1
ENV UV_LINK_MODE=copy
ENV UV_PROJECT_ENVIRONMENT=/app/.venv
ENV VIRTUAL_ENV=${UV_PROJECT_ENVIRONMENT}
ENV PYTHONPATH="/app/:/app/app/"
ENV PATH="/app/.venv/bin:${PATH}"
ENV DJANGO_SETTINGS_MODULE=conf.settings.production
ENV BASE_DIR="/app/app/"

RUN mkdir -p /app /app/staticfiles /app/mediafiles && \
    apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    postgresql-client \
    netcat-traditional \
    libmagic-dev \
    libproj-dev \
    libgeos-dev \
    gdal-bin \
    tini

WORKDIR /app

COPY uv.lock pyproject.toml /app/
RUN uv sync --frozen

COPY .. /app/
RUN uv run /app/app/manage.py collectstatic --noinput && \
    groupadd app && useradd -g app -d /app app && \
    chmod +x /app/conf/run.sh && \
    chown app -R /app

USER app

# Entrypoint
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["/app/conf/run.sh", "start"]
