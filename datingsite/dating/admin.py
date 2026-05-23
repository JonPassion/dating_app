from django.contrib import admin
from .models import UserProfile, Like, Pass, Match, Message, MediaGallery, Post

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'major', 'year', 'gender', 'created_at']
    list_filter = ['gender', 'year', 'major']
    search_fields = ['user__username', 'major', 'bio']

@admin.register(Pass)
class PassAdmin(admin.ModelAdmin):
    list_display = ['from_user', 'to_user', 'created_at']
    list_filter = ['created_at']


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ['from_user', 'to_user', 'created_at']
    list_filter = ['created_at']

@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ['user1', 'user2', 'created_at']
    list_filter = ['created_at']

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['sender', 'match', 'media_type', 'created_at', 'read']
    list_filter = ['created_at', 'read', 'media_type']
    search_fields = ['content']

@admin.register(MediaGallery)
class MediaGalleryAdmin(admin.ModelAdmin):
    list_display = ['user', 'media_type', 'caption', 'created_at']
    list_filter = ['media_type', 'created_at']
    search_fields = ['user__username', 'caption']

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['user', 'content_preview', 'created_at', 'like_count']
    list_filter = ['created_at']
    search_fields = ['user__username', 'content']
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'
    
    def like_count(self, obj):
        return obj.likes.count()
    like_count.short_description = 'Likes'
