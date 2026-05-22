import multiprocessing
import os

# Render sets PORT; Docker defaults to 8000
_port = os.environ.get('PORT', '8000')
bind = os.environ.get('GUNICORN_BIND', f'0.0.0.0:{_port}')
_default_workers = 1 if os.environ.get('RENDER') else (multiprocessing.cpu_count() * 2 + 1)
workers = int(os.environ.get('WEB_CONCURRENCY', _default_workers))
threads = int(os.environ.get('GUNICORN_THREADS', '2'))
worker_class = 'gthread'
timeout = int(os.environ.get('GUNICORN_TIMEOUT', '60'))
keepalive = 5
max_requests = int(os.environ.get('GUNICORN_MAX_REQUESTS', '1000'))
max_requests_jitter = 50
accesslog = '-'
errorlog = '-'
capture_output = True
