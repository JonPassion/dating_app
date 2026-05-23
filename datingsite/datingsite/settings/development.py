"""
Local development settings (SQLite, in-memory cache).
"""
from .base import *  # noqa: F403

DEBUG = True
ALLOWED_HOSTS = ['dating-app-v6l9.onrender.com', '127.0.0.1', 'localhost']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',  # noqa: F405
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unidate-dev',
    }
}

CORS_ALLOW_ALL_ORIGINS = True

SESSION_ENGINE = 'django.contrib.sessions.backends.db'
