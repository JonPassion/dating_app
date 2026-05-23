from django.db.models import Q
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile, Like, Pass, Match, Message, MediaGallery, Post


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']


class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = UserProfile
        fields = [
            'id', 'user', 'anonymous_id', 'bio', 'major', 'year',
            'interests', 'profile_picture', 'age', 'gender',
            'looking_for', 'anonymous_mode', 'hide_from_search',
            'created_at', 'updated_at'
        ]


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = [
            'bio', 'major', 'year', 'interests', 'profile_picture',
            'age', 'gender', 'looking_for', 'anonymous_mode', 'hide_from_search'
        ]


class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password']
    
    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        UserProfile.objects.create(user=user)
        return user


class LikeSerializer(serializers.ModelSerializer):
    from_user = UserSerializer(read_only=True)
    to_user = UserSerializer(read_only=True)
    
    class Meta:
        model = Like
        fields = ['id', 'from_user', 'to_user', 'created_at']


class MatchSerializer(serializers.ModelSerializer):
    user1 = UserSerializer(read_only=True)
    user2 = UserSerializer(read_only=True)
    other_user = serializers.SerializerMethodField()
    
    class Meta:
        model = Match
        fields = ['id', 'user1', 'user2', 'other_user', 'created_at']
    
    def get_other_user(self, obj):
        request = self.context.get('request')
        if request and request.user == obj.user1:
            return UserSerializer(obj.user2).data
        return UserSerializer(obj.user1).data


class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    media_url = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = ['id', 'match', 'sender', 'content', 'media_type', 'media_url', 'created_at', 'read']

    def get_media_url(self, obj):
        if not obj.media_file:
            return None
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(obj.media_file.url)
        return obj.media_file.url


class MediaGallerySerializer(serializers.ModelSerializer):
    class Meta:
        model = MediaGallery
        fields = ['id', 'media_type', 'file', 'caption', 'created_at']


class PostSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    like_count = serializers.IntegerField(read_only=True)
    is_liked = serializers.SerializerMethodField()
    
    class Meta:
        model = Post
        fields = ['id', 'user', 'content', 'created_at', 'like_count', 'is_liked']
    
    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.likes.filter(id=request.user.id).exists()
        return False


class BrowseUserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)
    is_matched = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'profile', 'is_matched', 'is_liked']
    
    def get_is_matched(self, obj):
        request = self.context.get('request')
        if not request:
            return False
        return Match.objects.filter(
            Q(user1=request.user, user2=obj) | Q(user1=obj, user2=request.user)
        ).exists()
    
    def get_is_liked(self, obj):
        request = self.context.get('request')
        if not request:
            return False
        return Like.objects.filter(from_user=request.user, to_user=obj).exists()


class DashboardStatsSerializer(serializers.Serializer):
    matches_count = serializers.IntegerField()
    likes_received = serializers.IntegerField()
    likes_given = serializers.IntegerField()
    unread_messages = serializers.IntegerField()
