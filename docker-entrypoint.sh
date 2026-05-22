#!/bin/sh
set -e
cd /app/datingsite
python manage.py migrate --noinput
exec "$@"
