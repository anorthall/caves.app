#!/bin/bash

SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$SCRIPT_DIR/.."
APP_ROOT="${PROJECT_ROOT}/app"

if [ -n "$DATABASE_URL" ]; then
    echo "Waiting for database to be ready..."
    DB_HOST=$(echo "$DATABASE_URL" | sed -E 's/^postgres:\/\/[^@]+@([^:]+):.*/\1/')
    DB_PORT=$(echo "$DATABASE_URL" | sed -E 's/^postgres:\/\/[^@]+@[^:]+:([0-9]+).*/\1/')
    DB_PORT=${DB_PORT:-5432}

    echo "Checking connection to $DB_HOST:$DB_PORT..."

    max_attempts=30
    counter=0
    until nc -z "$DB_HOST" "$DB_PORT"; do
        counter=$((counter + 1))
        if [ $counter -ge $max_attempts ]; then
            echo "Failed to connect to database after $max_attempts attempts. Exiting..."
            exit 1
        fi
        echo "Waiting for database... ($counter/$max_attempts)"
        sleep 1
    done

    echo "Database is ready!"
else
    echo "DATABASE_URL is not set. Exiting..."
    exit 1
fi

if [ "$1" = "manage" ]
then
    cd "$APP_ROOT" || exit 1
    uv run manage.py "${@:2}"
fi

if [ "$1" = "test" ]
then
    cd "$APP_ROOT" || exit 1
    uv run manage.py test "${@:2}"
    exit 0
fi

# Run a development server which runs workers within the same
# docker container within a separate process for quicker builds
# and less RAM usage.
if [ "$1" = "devserver" ]
then
    echo "Collecting static files..."
    cd "$APP_ROOT" || exit 1
    uv run manage.py collectstatic --noinput

    if [ "$RUN_MIGRATIONS_ON_START" = "yes" ]
    then
        echo "Running migrations..."
        uv run manage.py migrate --no-input
    fi

    cd "$PROJECT_ROOT" || exit 1

    uv run gunicorn \
      --bind "0.0.0.0:${PORT:-8000}" \
      --workers 2 \
      --reload \
      --reload-engine inotify \
      --name caves-django \
      conf.wsgi:application
fi

# Run production server
if [ "$1" = "start" ]
then
    NUM_CORES=$(nproc)
    NUM_WORKERS=$((NUM_CORES * 2 + 1))
    echo "Detected $NUM_CORES, running with $NUM_WORKERS workers"

    cd "$APP_ROOT" || exit 1
    uv run manage.py runmailer_pg &

    cd "$PROJECT_ROOT" || exit 1
    echo "Starting server..."
    uv run gunicorn \
      --bind "0.0.0.0:$PORT" \
      --workers "$NUM_WORKERS" \
      --preload \
      --max-requests 1000 \
      --max-requests-jitter 200 \
      --keep-alive 10 \
      --name caves-django \
      conf.wsgi:application
fi
