# syntax=docker/dockerfile:1
FROM python:3.11.3-alpine

# Environment setup
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
RUN mkdir -p /opt/dev
WORKDIR /opt/dev

# System packages
RUN apk update \
    && apk add postgresql-dev gcc python3-dev musl-dev

# Python packages
RUN pip install --upgrade pip
COPY ./requirements.txt .
RUN pip install -r requirements.txt

# Copy entrypoint
COPY ./etc/dev/entrypoint.dev.sh .
RUN chmod +x /opt/dev/entrypoint.dev.sh

# Copy app
COPY ./app/ /opt/dev/app/

# Final environment
WORKDIR /opt/dev/app

# Run entrypoint.sh.
ENTRYPOINT ["/opt/dev/entrypoint.dev.sh"]
