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


def get_all_browse_users(user, search_query=''):
    """
    Return all eligible browse users sorted by relevance:
      1. Same campus AND matches preference
      2. Matches preference only
      3. Same campus only
      4. Everyone else
    Users the current user already liked are shown last with a flag.
    """
    profile = get_user_profile(user)
    my_campus = (profile.campus or '').strip().lower()
    my_looking_for = profile.looking_for or ''

    excluded_ids = {user.id}
    hidden_ids = set(
        UserProfile.objects.filter(hide_from_search=True).values_list('user_id', flat=True)
    )
    liked_ids = set(
        Like.objects.filter(from_user=user).values_list('to_user_id', flat=True)
    )
    passed_ids = set(
        Pass.objects.filter(from_user=user).values_list('to_user_id', flat=True)
    )

    qs = (
        User.objects.filter(profile__isnull=False)
        .exclude(id__in=excluded_ids | hidden_ids)
        .select_related('profile')
    )

    if search_query:
        qs = qs.filter(username__icontains=search_query)

    all_users = list(qs)

    def sort_key(u):
        p = u.profile
        campus_match = bool(
            my_campus
            and (p.campus or '').strip().lower()
            and (p.campus or '').strip().lower() == my_campus
        )
        pref_match = (
            not my_looking_for
            or my_looking_for == 'both'
            or p.gender == my_looking_for
        )
        already_liked = u.id in liked_ids
        already_passed = u.id in passed_ids

        if already_liked or already_passed:
            tier = 4
        elif campus_match and pref_match:
            tier = 0
        elif pref_match:
            tier = 1
        elif campus_match:
            tier = 2
        else:
            tier = 3

        return (tier, u.username.lower())

    all_users.sort(key=sort_key)

    enriched = []
    for u in all_users:
        p = u.profile
        campus_match = bool(
            my_campus
            and (p.campus or '').strip().lower()
            and (p.campus or '').strip().lower() == my_campus
        )
        pref_match = (
            not my_looking_for
            or my_looking_for == 'both'
            or p.gender == my_looking_for
        )
        already_liked = u.id in liked_ids
        already_passed = u.id in passed_ids
        enriched.append({
            'user': u,
            'campus_match': campus_match,
            'pref_match': pref_match,
            'already_liked': already_liked,
            'already_passed': already_passed,
        })

    return enriched


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


CHAT_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
CHAT_VIDEO_EXTENSIONS = {'.mp4', '.webm', '.mov', '.m4v'}


def detect_chat_media_type(uploaded_file):
    """Return 'image' or 'video' for supported chat attachments, else None."""
    content_type = (getattr(uploaded_file, 'content_type', '') or '').lower()
    if content_type.startswith('image/'):
        return 'image'
    if content_type.startswith('video/'):
        return 'video'

    name = (getattr(uploaded_file, 'name', '') or '').lower()
    ext = '.' + name.rsplit('.', 1)[-1] if '.' in name else ''
    if ext in CHAT_IMAGE_EXTENSIONS:
        return 'image'
    if ext in CHAT_VIDEO_EXTENSIONS:
        return 'video'
    return None
