#!/bin/sh

if [ "$DATABASE" = "postgres" ]
then
    echo "Waiting for postgres..."

    while ! nc -z $SQL_HOST $SQL_PORT; do
      sleep 0.1
    done

    echo "PostgreSQL started"
fi

if [ "$RUN_MIGRATIONS" = "yes" ]
then
    echo "Running migrations..."
    python manage.py migrate
fi

if [ "$RUN_TESTS" = "yes" ]
then
    echo "Running tests..."
    python manage.py test
fi

exec "$@"
