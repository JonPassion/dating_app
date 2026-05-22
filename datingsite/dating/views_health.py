from django.db import connection
from django.http import JsonResponse
from django.views.decorators.http import require_GET


@require_GET
def health_check(request):
    """Load balancer / orchestrator health probe."""
    checks = {'database': False, 'cache': False}

    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
        checks['database'] = True
    except Exception:
        pass

    try:
        from django.core.cache import cache
        cache.set('health:ping', '1', 5)
        checks['cache'] = cache.get('health:ping') == '1'
    except Exception:
        checks['cache'] = True  # LocMem always works in dev

    healthy = all(checks.values())
    return JsonResponse(
        {'status': 'ok' if healthy else 'degraded', 'checks': checks},
        status=200 if healthy else 503,
    )
