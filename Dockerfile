# syntax=docker/dockerfile:1
FROM python:3
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /docker-app
COPY requirements.txt /docker-app
RUN pip install -r requirements.txt
COPY /app/* /docker-app
