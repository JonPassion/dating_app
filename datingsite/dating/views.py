from functools import wraps

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q
from django.views.decorators.http import require_POST, require_http_methods

from .models import UserProfile, Like, Pass, Match, Message, MediaGallery, Post
from .forms import UserProfileForm, UserRegisterForm, MediaUploadForm
from .utils import (
    get_user_profile,
    profile_complete,
    get_next_browse_user,
    get_all_browse_users,
    users_are_matched,
    display_name,
    get_dashboard_stats,
    invalidate_browse_cache,
    invalidate_dashboard_cache,
    detect_chat_media_type,
)


def profile_complete_required(view_func):
    @login_required
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        profile = get_user_profile(request.user)
        if not profile_complete(profile):
            messages.info(request, 'Please complete your profile before continuing.')
            return redirect('profile_edit')
        return view_func(request, *args, **kwargs)
    return wrapper


def home(request):
    if request.user.is_authenticated:
        profile = get_user_profile(request.user)
        if not profile_complete(profile):
            return redirect('profile_edit')
        return redirect('dashboard')
    return redirect('login')


@login_required
def dashboard(request):
    profile = get_user_profile(request.user)
    stats = get_dashboard_stats(request.user)
    matches_count = stats['matches_count']
    likes_received = stats['likes_received']
    likes_given = stats['likes_given']
    unread_messages = stats['unread_messages']

    recent_matches = Match.objects.filter(
        Q(user1=request.user) | Q(user2=request.user)
    ).select_related('user1', 'user2').order_by('-created_at')[:3]

    recent_posts = Post.objects.select_related('user', 'user__profile').order_by('-created_at')[:5]

    recent_chats = []
    for match in Match.objects.filter(
        Q(user1=request.user) | Q(user2=request.user)
    ).prefetch_related('messages'):
        other_user = match.user2 if match.user1 == request.user else match.user1
        last_message = match.messages.order_by('-created_at').first()
        if last_message:
            recent_chats.append({
                'match': match,
                'other_user': other_user,
                'other_display': display_name(other_user, request.user, is_matched=True),
                'last_message': last_message,
                'unread_count': match.messages.filter(sender=other_user, read=False).count(),
            })
    recent_chats.sort(key=lambda c: c['last_message'].created_at, reverse=True)
    recent_chats = recent_chats[:5]

    if request.method == 'POST' and 'create_post' in request.POST:
        content = (request.POST.get('content') or '').strip()
        if content:
            Post.objects.create(user=request.user, content=content)
            messages.success(request, 'Post created successfully!')
        else:
            messages.error(request, 'Post content cannot be empty.')
        return redirect('dashboard')

    return render(request, 'dating/dashboard.html', {
        'profile': profile,
        'matches_count': matches_count,
        'likes_received': likes_received,
        'likes_given': likes_given,
        'unread_messages': unread_messages,
        'recent_matches': recent_matches,
        'recent_posts': recent_posts,
        'recent_chats': recent_chats,
    })


def register(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            get_user_profile(user)
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}!')
            login(request, user)
            return redirect('profile_edit')
    else:
        form = UserRegisterForm()
    return render(request, 'dating/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            profile = get_user_profile(user)
            if not profile_complete(profile):
                messages.info(request, 'Welcome! Complete your profile to get started.')
                return redirect('profile_edit')
            return redirect('dashboard')
        messages.error(request, 'Invalid username or password.')
    return render(request, 'dating/login.html')


@login_required
@require_POST
def logout_view(request):
    logout(request)
    return redirect('home')


@login_required
def profile_edit(request):
    profile = get_user_profile(request.user)
    media_gallery = MediaGallery.objects.filter(user=request.user)

    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        media_form = MediaUploadForm(request.POST, request.FILES)

        if 'upload_media' in request.POST:
            if media_form.is_valid():
                media = media_form.save(commit=False)
                media.user = request.user
                media.save()
                messages.success(request, 'Media uploaded successfully!')
                return redirect('profile_edit')
            messages.error(request, 'Please fix the media upload errors.')
        elif form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated!')
            if profile_complete(profile):
                return redirect('profile_view')
            messages.info(request, 'Add gender, preference, and bio or major to finish your profile.')
            return redirect('profile_edit')
        else:
            messages.error(request, 'Please fix the errors below.')
    else:
        form = UserProfileForm(instance=profile)
        media_form = MediaUploadForm()

    return render(request, 'dating/profile_edit.html', {
        'form': form,
        'media_form': media_form,
        'media_gallery': media_gallery,
        'profile_complete': profile_complete(profile),
    })


@login_required
def profile_view(request):
    profile = get_user_profile(request.user)
    media_gallery = MediaGallery.objects.filter(user=request.user)
    return render(request, 'dating/profile_view.html', {
        'profile': profile,
        'media_gallery': media_gallery,
        'profile_complete': profile_complete(profile),
    })


@login_required
@profile_complete_required
def browse(request):
    search_query = request.GET.get('search', '').strip()
    my_profile = get_user_profile(request.user)

    enriched_users = get_all_browse_users(request.user, search_query)

    matched_ids = set(
        Match.objects.filter(
            Q(user1=request.user) | Q(user2=request.user)
        ).values_list('user1_id', 'user2_id')
        .__iter__()
    )
    flat_matched_ids = set()
    for pair in Match.objects.filter(
        Q(user1=request.user) | Q(user2=request.user)
    ).values_list('user1_id', 'user2_id'):
        flat_matched_ids.update(pair)
    flat_matched_ids.discard(request.user.id)

    for entry in enriched_users:
        u = entry['user']
        is_matched = u.id in flat_matched_ids
        entry['is_matched'] = is_matched
        entry['display_name'] = display_name(u, request.user, is_matched=is_matched)

    return render(request, 'dating/browse.html', {
        'enriched_users': enriched_users,
        'search_query': search_query,
        'my_profile': my_profile,
    })


@login_required
@profile_complete_required
@require_POST
def like_user(request, user_id):
    to_user = get_object_or_404(User, id=user_id)

    if to_user == request.user:
        return redirect('browse')

    Pass.objects.filter(from_user=request.user, to_user=to_user).delete()
    Like.objects.get_or_create(from_user=request.user, to_user=to_user)

    if Like.objects.filter(from_user=to_user, to_user=request.user).exists():
        match, created = Match.objects.get_or_create(
            user1=min(request.user, to_user, key=lambda u: u.id),
            user2=max(request.user, to_user, key=lambda u: u.id),
        )
        if created:
            messages.success(
                request,
                f"You matched with {display_name(to_user, request.user, is_matched=True)}!",
            )
            invalidate_dashboard_cache(request.user.id)
            invalidate_dashboard_cache(to_user.id)

    invalidate_browse_cache(request.user.id)
    return redirect('browse')


@login_required
@profile_complete_required
@require_POST
def dislike_user(request, user_id):
    to_user = get_object_or_404(User, id=user_id)
    if to_user != request.user:
        Pass.objects.get_or_create(from_user=request.user, to_user=to_user)
        Like.objects.filter(from_user=request.user, to_user=to_user).delete()
        invalidate_browse_cache(request.user.id)
    return redirect('browse')


@login_required
@profile_complete_required
def matches(request):
    match_list = Match.objects.filter(
        Q(user1=request.user) | Q(user2=request.user)
    ).select_related('user1', 'user2', 'user1__profile', 'user2__profile')

    enriched = []
    for match in match_list:
        other = match.user2 if match.user1 == request.user else match.user1
        enriched.append({
            'match': match,
            'other_user': other,
            'display_name': display_name(other, request.user, is_matched=True),
        })

    return render(request, 'dating/matches.html', {'match_entries': enriched})


@login_required
@profile_complete_required
@require_http_methods(['GET', 'POST'])
def chat(request, match_id):
    match = get_object_or_404(Match, id=match_id)

    if match.user1 != request.user and match.user2 != request.user:
        return redirect('matches')

    other_user = match.user2 if match.user1 == request.user else match.user1
    messages_list = match.messages.select_related('sender').order_by('created_at')

    updated = match.messages.filter(sender=other_user, read=False).update(read=True)
    if updated:
        invalidate_dashboard_cache(request.user.id)

    if request.method == 'POST':
        content = (request.POST.get('content') or '').strip()
        media_file = request.FILES.get('media')
        media_type = ''

        if media_file:
            media_type = detect_chat_media_type(media_file)
            if not media_type:
                messages.error(request, 'Unsupported file type. Use an image or video.')
                return render(request, 'dating/chat.html', {
                    'match': match,
                    'other_user': other_user,
                    'other_display': display_name(other_user, request.user, is_matched=True),
                    'messages': messages_list,
                })

        if content or media_file:
            Message.objects.create(
                match=match,
                sender=request.user,
                content=content,
                media_type=media_type,
                media_file=media_file if media_file else None,
            )
            invalidate_dashboard_cache(match.user1_id)
            invalidate_dashboard_cache(match.user2_id)
            return redirect('chat', match_id=match.id)
        messages.error(request, 'Message cannot be empty.')

    return render(request, 'dating/chat.html', {
        'match': match,
        'other_user': other_user,
        'other_display': display_name(other_user, request.user, is_matched=True),
        'messages': messages_list,
    })


@login_required
@require_POST
def delete_media(request, media_id):
    media = get_object_or_404(MediaGallery, id=media_id, user=request.user)
    media.delete()
    messages.success(request, 'Media deleted successfully!')
    return redirect('profile_edit')


@login_required
@profile_complete_required
def view_profile(request, user_id):
    user = get_object_or_404(User, id=user_id)
    profile = get_object_or_404(UserProfile, user=user)
    is_matched = users_are_matched(request.user, user)
    is_own_profile = user == request.user
    can_see_full = is_own_profile or is_matched or not profile.anonymous_mode

    media_gallery = MediaGallery.objects.filter(user=user) if can_see_full else []

    return render(request, 'dating/view_profile.html', {
        'profile': profile,
        'user': user,
        'is_matched': is_matched,
        'is_own_profile': is_own_profile,
        'can_see_full': can_see_full,
        'display_name': display_name(user, request.user, is_matched=is_matched),
        'media_gallery': media_gallery,
    })


@login_required
@require_POST
def like_post_view(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.user in post.likes.all():
        post.likes.remove(request.user)
    else:
        post.likes.add(request.user)
    return redirect('dashboard')
