#!/bin/bash

DB_URL_STR="${DATABASE_URL:-postgres://postgres:postgres@db:5432/postgres}"
DB_HOST="$(echo "$DB_URL_STR" | cut -d'@' -f2 | cut -d':' -f1)"
DB_PORT="$(echo "$DB_URL_STR" | cut -d'@' -f2 | cut -d':' -f2 | cut -d'/' -f1)"

while ! nc -z "$DB_HOST" "$DB_PORT"; do
  sleep 0.1
done
echo "PostgreSQL running..."

if [ "$1" = "migrate" ]
then
    echo "Running migrations..."
    python src/manage.py migrate --no-input
fi

if [ "$1" = "test" ]
then
    echo "Running tests..."
    cd /app/src/ || exit 1
    python manage.py test
fi

if [ "$1" = "manage" ]
then
    python src/manage.py "${@:2}"
fi

if [ "$1" = "devserver" ]
then
    echo "Collecting static files..."
    python src/manage.py collectstatic --noinput

    echo "Running migrations..."
    python src/manage.py migrate --no-input

    echo "Starting development server..."
    python src/manage.py runserver 0.0.0.0:"${PORT:=8000}" --insecure
fi

if [ "$1" = "start" ]
then
    echo "Collecting static files..."
    python src/manage.py collectstatic --noinput

    if [ "$RUN_MIGRATIONS_ON_START" = "yes" ]
    then
        echo "Running migrations..."
        python src/manage.py migrate --no-input
    fi

    # Calculate gunicorn workers (CPU cores * 2 + 1)
    CPU_CORES=$(nproc --all)
    WORKERS=$((CPU_CORES * 2 + 1))
    echo "Detected $CPU_CORES CPU cores. Defaulting to $WORKERS gunicorn workers."

    echo "Starting server..."
    gunicorn config.django.wsgi:application --bind 0.0.0.0:"${PORT:=8000}" --workers "$WORKERS"
fi
