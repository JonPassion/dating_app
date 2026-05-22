FROM python:3.13-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_ENV=production

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt gunicorn.conf.py docker-entrypoint.sh /app/
RUN pip install --no-cache-dir -r requirements.txt && chmod +x /app/docker-entrypoint.sh

COPY datingsite/ ./datingsite/

WORKDIR /app/datingsite

RUN DJANGO_ENV=development python manage.py collectstatic --noinput

EXPOSE 8000

ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["gunicorn", "datingsite.wsgi:application", "-c", "/app/gunicorn.conf.py"]
