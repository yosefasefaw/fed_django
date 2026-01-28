#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

echo "--- 🚀 Starting Entrypoint Script ---"

# Wait for the database to be ready
# We use environment variables so this works on both Local and Railway
DB_HOST=${POSTGRES_HOST:-db}
DB_PORT=${POSTGRES_PORT:-5432}

echo "Waiting for database at $DB_HOST:$DB_PORT..."
while ! uv run python -c "import socket; s = socket.socket(socket.AF_INET, socket.SOCK_STREAM); s.connect(('$DB_HOST', $DB_PORT))" > /dev/null 2>&1; do
  sleep 1
done
echo "Database is up!"

# --- ONLY THE WEB CONTAINER RUNS THESE SETUP STEPS ---
if [ "$1" != "scheduler" ]; then
    # Apply database migrations
    echo "Applying database migrations..."
    uv run python manage.py migrate --noinput

    # Collect static files (Necessary for WhiteNoise)
    echo "Collecting static files..."
    uv run python manage.py collectstatic --noinput --clear
fi

# Check what we are supposed to run
if [ "$1" = "scheduler" ]; then
    echo "Starting FOMC Scheduler..."
    uv run python scheduler.py
else
    echo "Starting Django Web Server with Gunicorn..."
    uv run gunicorn core.wsgi:application --bind 0.0.0.0:8000 --workers 3
fi
