#!/usr/bin/env bash
# Render.com build script (free tier)
set -o errexit

pip install --upgrade pip
pip install -r requirements.txt

cd datingsite

python manage.py collectstatic --noinput
python manage.py migrate --noinput

# Database cache table (used when Redis is not available on free tier)
python manage.py createcachetable 2>/dev/null || true
