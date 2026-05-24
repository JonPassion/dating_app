from django.utils import timezone


class UpdateLastSeenMiddleware:
    """Update UserProfile.last_seen on every authenticated request."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.user.is_authenticated:
            try:
                from .models import UserProfile
                UserProfile.objects.filter(user=request.user).update(last_seen=timezone.now())
            except Exception:
                pass
        return response
