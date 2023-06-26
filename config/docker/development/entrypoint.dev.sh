#!/bin/sh

if [ "$SQL_ENGINE" = "django.db.backends.postgresql" ]
then
    echo "Waiting for postgres..."

    while ! nc -z "$SQL_HOST" "$SQL_PORT"; do
      sleep 0.1
    done

    echo "PostgreSQL started"
fi

if [ "$RUN_MIGRATIONS" = "yes" ]
then
    echo "Running migrations..."
    python manage.py migrate
fi

exec "$@"
