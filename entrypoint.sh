#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

echo "--- 🚀 Starting Entrypoint Script ---"

# Wait for the database to be ready
echo "Waiting for database..."
while ! uv run python -c "import socket; s = socket.socket(socket.AF_INET, socket.SOCK_STREAM); s.connect(('db', 5432))" > /dev/null 2>&1; do
  sleep 1
done
echo "Database is up!"

# Apply database migrations
echo "Applying database migrations..."
uv run python manage.py migrate --noinput

# Collect static files (optional but good for production)
echo "Collecting static files..."
uv run python manage.py collectstatic --noinput || true

# Check what we are supposed to run
if [ "$1" = "scheduler" ]; then
    echo "Starting FOMC Scheduler..."
    uv run python scheduler.py
else
    echo "Starting Django Web Server..."
    uv run python manage.py runserver 0.0.0.0:8000
fi
