from django.urls import path
from . import views, api_views

urlpatterns = [
    # Web Routes
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile_view'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('profile/media/delete/<int:media_id>/', views.delete_media, name='delete_media'),
    path('browse/', views.browse, name='browse'),
    path('like/<int:user_id>/', views.like_user, name='like_user'),
    path('dislike/<int:user_id>/', views.dislike_user, name='dislike_user'),
    path('matches/', views.matches, name='matches'),
    path('chat/<int:match_id>/', views.chat, name='chat'),
    path('profile/<int:user_id>/', views.view_profile, name='view_profile'),
    path('posts/<int:post_id>/like/', views.like_post_view, name='like_post'),
    
    # API Routes
    path('api/auth/register/', api_views.RegisterView.as_view(), name='api_register'),
    path('api/auth/login/', api_views.CustomTokenObtainPairView.as_view(), name='api_login'),
    path('api/auth/refresh/', api_views.TokenRefreshView.as_view(), name='api_token_refresh'),
    path('api/profile/', api_views.ProfileView.as_view(), name='api_profile'),
    path('api/profile/<int:user_id>/', api_views.UserProfileDetailView.as_view(), name='api_user_profile'),
    path('api/dashboard/stats/', api_views.dashboard_stats, name='api_dashboard_stats'),
    path('api/browse/', api_views.browse_users, name='api_browse'),
    path('api/like/<int:user_id>/', api_views.like_user, name='api_like'),
    path('api/dislike/<int:user_id>/', api_views.dislike_user, name='api_dislike'),
    path('api/matches/', api_views.MatchListView.as_view(), name='api_matches'),
    path('api/chat/<int:match_id>/', api_views.chat_messages, name='api_chat'),
    path('api/posts/', api_views.PostListCreateView.as_view(), name='api_posts'),
    path('api/posts/<int:post_id>/like/', api_views.like_post, name='api_like_post'),
    path('api/media/', api_views.MediaGalleryListCreateView.as_view(), name='api_media'),
    path('api/media/<int:pk>/', api_views.MediaGalleryDeleteView.as_view(), name='api_media_delete'),
]