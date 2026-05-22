"""
Production settings — Docker, Render, and other hosts.
"""
import os

from .base import *  # noqa: F403

DEBUG = False

SECRET_KEY = os.environ['DJANGO_SECRET_KEY']

# --- Hosts (Render auto-injects RENDER_EXTERNAL_HOSTNAME) ---
ALLOWED_HOSTS = [
    h.strip()
    for h in os.environ.get('DJANGO_ALLOWED_HOSTS', '').split(',')
    if h.strip()
]
render_host = os.environ.get('RENDER_EXTERNAL_HOSTNAME', '').strip()
if render_host:
    ALLOWED_HOSTS.append(render_host)
if not ALLOWED_HOSTS:
    raise ValueError(
        'Set DJANGO_ALLOWED_HOSTS or deploy on Render (RENDER_EXTERNAL_HOSTNAME).'
    )

CSRF_TRUSTED_ORIGINS = [
    f'https://{host}'
    for host in ALLOWED_HOSTS
    if host and not host.startswith('.')
]
render_url = os.environ.get('RENDER_EXTERNAL_URL', '').strip()
if render_url:
    CSRF_TRUSTED_ORIGINS.append(render_url.rstrip('/'))

# --- Database (Render DATABASE_URL or manual Postgres vars) ---
database_url = os.environ.get('DATABASE_URL', '').strip()
if database_url:
    import dj_database_url
    DATABASES = {
        'default': dj_database_url.config(
            default=database_url,
            conn_max_age=int(os.environ.get('DB_CONN_MAX_AGE', '60')),
            ssl_require=not database_url.startswith('postgres://127.'),
        )
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('POSTGRES_DB', 'unidate'),
            'USER': os.environ.get('POSTGRES_USER', 'unidate'),
            'PASSWORD': os.environ.get('POSTGRES_PASSWORD', ''),
            'HOST': os.environ.get('POSTGRES_HOST', 'db'),
            'PORT': os.environ.get('POSTGRES_PORT', '5432'),
            'CONN_MAX_AGE': int(os.environ.get('DB_CONN_MAX_AGE', '60')),
            'OPTIONS': {'connect_timeout': 10},
        }
    }

# --- Cache & sessions: Redis if available, else DB (Render free tier) ---
REDIS_URL = os.environ.get('REDIS_URL', '').strip()
if REDIS_URL:
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': REDIS_URL,
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                'SOCKET_CONNECT_TIMEOUT': 5,
                'SOCKET_TIMEOUT': 5,
                'IGNORE_EXCEPTIONS': True,
            },
            'KEY_PREFIX': 'unidate',
        }
    }
    SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
    SESSION_CACHE_ALIAS = 'default'
else:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
            'LOCATION': 'django_cache_table',
        }
    }
    SESSION_ENGINE = 'django.contrib.sessions.backends.db'

# --- Security (Render terminates TLS at the edge) ---
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = os.environ.get('SECURE_SSL_REDIRECT', 'true').lower() in ('1', 'true', 'yes')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

CORS_ALLOWED_ORIGINS = [
    o.strip()
    for o in os.environ.get('CORS_ALLOWED_ORIGINS', '').split(',')
    if o.strip()
]
if render_url and render_url not in CORS_ALLOWED_ORIGINS:
    CORS_ALLOWED_ORIGINS.append(render_url.rstrip('/'))

# --- Static files (WhiteNoise — no separate static host on Render free tier) ---
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')  # noqa: F405
STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        # Manifest storage can fail deploy if assets change; safer on PaaS:
        'BACKEND': 'whitenoise.storage.CompressedStaticFilesStorage',
    },
}

# --- Logging ---
LOGGING['handlers']['console']['level'] = 'WARNING'  # noqa: F405
