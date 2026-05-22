import random

from django.conf import settings
from django.contrib.auth.models import User
from django.core.cache import cache
from django.db.models import Q

from .models import UserProfile, Like, Pass, Match, Message


def get_user_profile(user):
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return profile


def profile_complete(profile):
    return bool(
        profile.gender
        and profile.looking_for
        and ((profile.bio or '').strip() or (profile.major or '').strip())
    )


def display_name(user, viewer, is_matched=False):
    if user == viewer:
        return user.username
    try:
        profile = user.profile
    except UserProfile.DoesNotExist:
        return user.username
    if profile.anonymous_mode and not is_matched:
        return f"User #{profile.anonymous_id}"
    return user.username


def _excluded_cache_key(user_id):
    return f'browse:excluded:{user_id}'


def get_excluded_user_ids(user):
    """Cached set of user IDs to skip in browse (likes, passes, self)."""
    key = _excluded_cache_key(user.id)
    excluded = cache.get(key)
    if excluded is None:
        liked = set(
            Like.objects.filter(from_user_id=user.id).values_list('to_user_id', flat=True)
        )
        passed = set(
            Pass.objects.filter(from_user_id=user.id).values_list('to_user_id', flat=True)
        )
        excluded = liked | passed | {user.id}
        cache.set(key, excluded, settings.BROWSE_EXCLUDED_CACHE_TTL)
    return excluded


def invalidate_browse_cache(user_id):
    cache.delete(_excluded_cache_key(user_id))


def get_browse_candidate_ids(user, search_query=''):
    """Return eligible user IDs for browse (indexed queries, no random sort)."""
    profile = get_user_profile(user)
    excluded = get_excluded_user_ids(user)

    qs = (
        User.objects.filter(profile__isnull=False)
        .exclude(profile__hide_from_search=True)
        .exclude(id__in=excluded)
        .values_list('id', flat=True)
    )

    if search_query:
        qs = qs.filter(username__icontains=search_query)
    elif profile.looking_for and profile.looking_for != 'both':
        qs = qs.filter(profile__gender=profile.looking_for)

    return list(qs[:2000])


def get_next_browse_user(user, search_query=''):
    """
    Pick one random eligible user by ID list (scales to thousands of users).
    Replaces order_by('?') which forces full table scans.
    """
    candidate_ids = get_browse_candidate_ids(user, search_query)
    if not candidate_ids:
        return None
    chosen_id = random.choice(candidate_ids)
    return User.objects.select_related('profile').get(pk=chosen_id)


def users_are_matched(user_a, user_b):
    return Match.objects.filter(
        Q(user1=user_a, user2=user_b) | Q(user1=user_b, user2=user_a)
    ).exists()


def get_dashboard_stats(user):
    """Cached dashboard counters to reduce repeated aggregate queries."""
    key = f'dashboard:stats:{user.id}'
    stats = cache.get(key)
    if stats is not None:
        return stats

    match_ids = list(
        Match.objects.filter(Q(user1=user) | Q(user2=user)).values_list('id', flat=True)
    )

    stats = {
        'matches_count': len(match_ids),
        'likes_received': Like.objects.filter(to_user=user).count(),
        'likes_given': Like.objects.filter(from_user=user).count(),
        'unread_messages': (
            Message.objects.filter(match_id__in=match_ids, read=False)
            .exclude(sender=user)
            .count()
            if match_ids
            else 0
        ),
    }
    cache.set(key, stats, settings.DASHBOARD_STATS_CACHE_TTL)
    return stats


def invalidate_dashboard_cache(user_id):
    cache.delete(f'dashboard:stats:{user_id}')
