#!/bin/sh

if [ "$DATABASE" = "postgres" ]
then
    echo "Waiting for postgres..."

    while ! nc -z $SQL_HOST $SQL_PORT; do
      sleep 0.1
    done

    echo "PostgreSQL started"
fi

if [ "$COLLECT_STATIC" = "yes" ]
then
    echo "Collecting static files..."
    python manage.py collectstatic --no-input
fi

exec "$@"
