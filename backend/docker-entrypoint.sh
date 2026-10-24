#!/bin/sh
# Docker entrypoint script for ATS backend
# Runs Alembic migrations before starting the application server (per D-16)
set -e

echo "Running database migrations..."
alembic upgrade head

echo "Starting ATS API server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
