#!/bin/bash
set -e

echo "Applying multi-db migrations..."

python manage.py migrate --database=default --noinput
python manage.py migrate --database=transformation --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting Gunicorn..."
exec gunicorn config.wsgi:application -c gunicorn.conf.py

