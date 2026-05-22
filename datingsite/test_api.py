#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'datingsite.settings')
django.setup()

from django.contrib.auth.models import User
from dating.models import UserProfile

# Create test users
if User.objects.filter(username='testuser').exists():
    print("Test user already exists")
else:
    user1 = User.objects.create_user('testuser', 'test@test.com', 'testpass123')
    UserProfile.objects.create(user=user1, bio='Test user bio', age=22, gender='male', looking_for='female')
    print(f"Created test user: {user1.username}")

if User.objects.filter(username='testuser2').exists():
    print("Test user 2 already exists")
else:
    user2 = User.objects.create_user('testuser2', 'test2@test.com', 'testpass123')
    UserProfile.objects.create(user=user2, bio='Test user 2 bio', age=21, gender='female', looking_for='male')
    print(f"Created test user 2: {user2.username}")

print(f"\nTotal users: {User.objects.count()}")
print("\nTest credentials:")
print("  User 1: testuser / testpass123")
print("  User 2: testuser2 / testpass123")
