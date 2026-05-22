from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.urls import reverse

from .models import UserProfile, Like, Pass, Match
from .utils import get_browse_candidate_ids, profile_complete, display_name, invalidate_browse_cache


class ProfileUtilsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('alice', 'a@test.com', 'pass12345')
        self.profile = UserProfile.objects.get(user=self.user)

    def test_profile_incomplete_by_default(self):
        self.assertFalse(profile_complete(self.profile))

    def test_profile_complete_when_filled(self):
        self.profile.gender = 'female'
        self.profile.looking_for = 'male'
        self.profile.bio = 'Hello'
        self.profile.save()
        self.assertTrue(profile_complete(self.profile))


class BrowseFlowTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.u1 = User.objects.create_user('u1', '1@test.com', 'pass12345')
        self.u2 = User.objects.create_user('u2', '2@test.com', 'pass12345')
        for u, gender, looking in [
            (self.u1, 'male', 'female'),
            (self.u2, 'female', 'male'),
        ]:
            p = UserProfile.objects.get(user=u)
            p.gender = gender
            p.looking_for = looking
            p.bio = 'Bio'
            p.save()
        self.client.login(username='u1', password='pass12345')

    def test_pass_excludes_user_from_browse(self):
        Pass.objects.create(from_user=self.u1, to_user=self.u2)
        invalidate_browse_cache(self.u1.id)
        ids = get_browse_candidate_ids(self.u1)
        self.assertNotIn(self.u2.id, ids)

    def test_dislike_via_post_creates_pass(self):
        response = self.client.post(reverse('dislike_user', args=[self.u2.id]))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Pass.objects.filter(from_user=self.u1, to_user=self.u2).exists())

    def test_mutual_like_creates_match(self):
        Like.objects.create(from_user=self.u2, to_user=self.u1)
        self.client.post(reverse('like_user', args=[self.u2.id]))
        self.assertTrue(
            Match.objects.filter(user1=self.u1, user2=self.u2).exists()
            or Match.objects.filter(user1=self.u2, user2=self.u1).exists()
        )


class AnonymousDisplayTests(TestCase):
    def setUp(self):
        self.viewer = User.objects.create_user('viewer', 'v@test.com', 'pass12345')
        self.target = User.objects.create_user('target', 't@test.com', 'pass12345')
        self.target_profile = UserProfile.objects.get(user=self.target)
        UserProfile.objects.filter(user=self.target).update(
            anonymous_mode=True,
            anonymous_id='ABC123',
        )
        self.target_profile.refresh_from_db()

    def test_anonymous_name_before_match(self):
        name = display_name(self.target, self.viewer, is_matched=False)
        self.assertTrue(name.startswith('User #'))
        self.assertNotEqual(name, self.target.username)

    def test_real_name_after_match(self):
        name = display_name(self.target, self.viewer, is_matched=True)
        self.assertEqual(name, 'target')
