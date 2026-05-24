from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth.models import User
from django.db import models
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .models import Like, Pass, Match, Message, MediaGallery, Post, UserProfile
from .serializers import (
    UserSerializer, UserProfileSerializer, UserProfileUpdateSerializer,
    UserRegisterSerializer, MatchSerializer, MessageSerializer,
    MediaGallerySerializer, PostSerializer, BrowseUserSerializer, DashboardStatsSerializer,
)
from .utils import (
    get_user_profile,
    profile_complete,
    get_next_browse_user,
    invalidate_browse_cache,
    invalidate_dashboard_cache,
    get_dashboard_stats,
    detect_chat_media_type,
)


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                'user': UserSerializer(user).data,
                'message': 'User created successfully',
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            username = request.data.get('username')
            if username:
                try:
                    user = User.objects.get(username=username)
                    response.data['user'] = UserSerializer(user).data
                except User.DoesNotExist:
                    pass
        return response


class ProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return get_user_profile(self.request.user)

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return UserProfileUpdateSerializer
        return UserProfileSerializer


class UserProfileDetailView(generics.RetrieveAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = UserProfile.objects.select_related('user')
    lookup_field = 'user_id'
    lookup_url_kwarg = 'user_id'


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def dashboard_stats(request):
    data = get_dashboard_stats(request.user)

    serializer = DashboardStatsSerializer(data)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def browse_users(request):
    user = request.user
    profile = get_user_profile(user)
    if not profile_complete(profile):
        return Response(
            {'error': 'Complete your profile before browsing.'},
            status=status.HTTP_403_FORBIDDEN,
        )

    search_query = request.query_params.get('search', '').strip()
    next_user = get_browse_queryset(user, search_query).first()

    if next_user:
        serializer = BrowseUserSerializer(next_user, context={'request': request})
        return Response({'user': serializer.data})

    return Response({'user': None})


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def like_user(request, user_id):
    try:
        to_user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

    if to_user == request.user:
        return Response({'error': 'Cannot like yourself'}, status=status.HTTP_400_BAD_REQUEST)

    Pass.objects.filter(from_user=request.user, to_user=to_user).delete()
    Like.objects.get_or_create(from_user=request.user, to_user=to_user)

    is_match = False
    if Like.objects.filter(from_user=to_user, to_user=request.user).exists():
        _, match_created = Match.objects.get_or_create(
            user1=min(request.user, to_user, key=lambda u: u.id),
            user2=max(request.user, to_user, key=lambda u: u.id),
        )
        is_match = match_created
        if is_match:
            invalidate_dashboard_cache(request.user.id)
            invalidate_dashboard_cache(to_user.id)

    invalidate_browse_cache(request.user.id)
    return Response({
        'liked': True,
        'is_match': is_match,
        'message': 'You have a new match!' if is_match else 'Liked successfully',
    })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def dislike_user(request, user_id):
    try:
        to_user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

    if to_user != request.user:
        Pass.objects.get_or_create(from_user=request.user, to_user=to_user)
        Like.objects.filter(from_user=request.user, to_user=to_user).delete()
        invalidate_browse_cache(request.user.id)

    return Response({'passed': True})


class MatchListView(generics.ListAPIView):
    serializer_class = MatchSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Match.objects.filter(
            models.Q(user1=user) | models.Q(user2=user)
        ).order_by('-created_at')

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


@api_view(['GET', 'POST'])
@permission_classes([permissions.IsAuthenticated])
def chat_messages(request, match_id):
    try:
        match = Match.objects.get(id=match_id)
    except Match.DoesNotExist:
        return Response({'error': 'Match not found'}, status=status.HTTP_404_NOT_FOUND)

    if match.user1 != request.user and match.user2 != request.user:
        return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'POST':
        content = (request.data.get('content') or '').strip()
        media_file = request.FILES.get('media') or request.FILES.get('media_file')
        if not content and not media_file:
            return Response(
                {'error': 'Message text or media is required'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        media_type = ''
        if media_file:
            media_type = detect_chat_media_type(media_file)
            if not media_type:
                return Response(
                    {'error': 'Unsupported file type. Use an image or video.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        message = Message.objects.create(
            match=match,
            sender=request.user,
            content=content,
            media_type=media_type,
            media_file=media_file if media_file else None,
        )
        invalidate_dashboard_cache(match.user1_id)
        invalidate_dashboard_cache(match.user2_id)
        return Response(
            MessageSerializer(message, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )

    messages_qs = Message.objects.filter(match=match).order_by('created_at')
    messages_qs.filter(read=False).exclude(sender=request.user).update(read=True)

    after = request.query_params.get('after')
    incremental = False
    if after:
        try:
            after_id = int(after)
            messages_qs = messages_qs.filter(id__gt=after_id)
            incremental = True
        except (TypeError, ValueError):
            pass

    other_user = match.user2 if match.user1 == request.user else match.user1

    return Response({
        'messages': MessageSerializer(
            messages_qs, many=True, context={'request': request}
        ).data,
        'other_user': UserSerializer(other_user).data,
        'match_id': match.id,
        'incremental': incremental,
    })


class PostListCreateView(generics.ListCreateAPIView):
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Post.objects.select_related('user').order_by('-created_at')[:20]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def like_post(request, post_id):
    try:
        post = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        return Response({'error': 'Post not found'}, status=status.HTTP_404_NOT_FOUND)

    if request.user in post.likes.all():
        post.likes.remove(request.user)
        return Response({'liked': False, 'like_count': post.likes.count()})
    post.likes.add(request.user)
    return Response({'liked': True, 'like_count': post.likes.count()})


class MediaGalleryListCreateView(generics.ListCreateAPIView):
    serializer_class = MediaGallerySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return MediaGallery.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class MediaGalleryDeleteView(generics.DestroyAPIView):
    serializer_class = MediaGallerySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return MediaGallery.objects.filter(user=self.request.user)



@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def ping_online(request):
    """Update last_seen timestamp so the user appears active."""
    from django.utils import timezone
    UserProfile.objects.filter(user=request.user).update(last_seen=timezone.now())
    return Response({'status': 'ok'})
