from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from datetime import timedelta

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    anonymous_id = models.CharField(max_length=10, unique=True, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    major = models.CharField(max_length=100, blank=True)
    year = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(6)],
        blank=True, null=True,
        help_text="Year of study (1-6)"
    )
    interests = models.TextField(
        blank=True,
        help_text="Comma-separated list of interests"
    )
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    age = models.IntegerField(
        validators=[MinValueValidator(16), MaxValueValidator(100)],
        blank=True, null=True
    )
    gender = models.CharField(
        max_length=20,
        choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other'), ('prefer_not_to_say', 'Prefer not to say')],
        blank=True
    )
    looking_for = models.CharField(
        max_length=20,
        choices=[('male', 'Male'), ('female', 'Female'), ('both', 'Both'), ('other', 'Other')],
        blank=True
    )
    campus = models.CharField(
        max_length=150,
        blank=True,
        help_text="University campus or location"
    )
    anonymous_mode = models.BooleanField(
        default=True,
        help_text="Hide username and use anonymous ID"
    )
    hide_from_search = models.BooleanField(
        default=False,
        help_text="Don't appear in browse results"
    )
    last_seen = models.DateTimeField(
        null=True, blank=True,
        help_text="Last time the user was active"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['hide_from_search', 'gender']),
            models.Index(fields=['-updated_at']),
            models.Index(fields=['-last_seen']),
        ]

    def __str__(self):
        return f"{self.user.username}'s profile"

    @property
    def is_online(self):
        if not self.last_seen:
            return False
        return timezone.now() - self.last_seen < timedelta(minutes=5)

    def is_complete(self):
        return bool(
            self.gender
            and self.looking_for
            and ((self.bio or '').strip() or (self.major or '').strip())
        )

    def save(self, *args, **kwargs):
        if not self.anonymous_id:
            import random
            import string
            while True:
                anon_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
                if not UserProfile.objects.filter(anonymous_id=anon_id).exists():
                    self.anonymous_id = anon_id
                    break
        super().save(*args, **kwargs)

class Pass(models.Model):
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='passes_given')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='passes_received')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('from_user', 'to_user')
        indexes = [
            models.Index(fields=['from_user', 'to_user']),
            models.Index(fields=['from_user', '-created_at']),
        ]

    def __str__(self):
        return f"{self.from_user.username} passed on {self.to_user.username}"


class Like(models.Model):
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='likes_given')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='likes_received')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('from_user', 'to_user')
        indexes = [
            models.Index(fields=['from_user', 'to_user']),
            models.Index(fields=['to_user', '-created_at']),
            models.Index(fields=['from_user', '-created_at']),
        ]

    def __str__(self):
        return f"{self.from_user.username} likes {self.to_user.username}"


class Match(models.Model):
    user1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='matches_as_user1')
    user2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='matches_as_user2')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user1', 'user2')
        indexes = [
            models.Index(fields=['user1', 'user2']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f"Match between {self.user1.username} and {self.user2.username}"


class Message(models.Model):
    MEDIA_TYPES = [
        ('image', 'Image'),
        ('video', 'Video'),
    ]

    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField(blank=True, default='')
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPES, blank=True, default='')
    media_file = models.FileField(upload_to='chat_media/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=['match', '-created_at']),
            models.Index(fields=['match', 'read', 'sender']),
        ]
        ordering = ['created_at']

    def __str__(self):
        return f"Message from {self.sender.username}"


class MediaGallery(models.Model):
    MEDIA_TYPES = [
        ('image', 'Image'),
        ('video', 'Video'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='media_gallery')
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPES)
    file = models.FileField(upload_to='media_gallery/')
    caption = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username}'s {self.get_media_type_display()}"

class Post(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    content = models.TextField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    likes = models.ManyToManyField(User, related_name='liked_posts', blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['user', '-created_at']),
        ]

    def __str__(self):
        return f"Post by {self.user.username}"

    def like_count(self):
        return self.likes.count()
