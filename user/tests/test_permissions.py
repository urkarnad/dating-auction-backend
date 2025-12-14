from django.test import TestCase
from rest_framework.test import APIRequestFactory
from user.permissions import NotBanned
from django.contrib.auth import get_user_model

User = get_user_model()


class NotBannedPermissionTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.perm = NotBanned()

    def test_allows_not_banned_user(self):
        u = User.objects.create_user(email="u@ukma.edu.ua", password="x")
        u.is_banned = False
        request = self.factory.get("/")
        request.user = u
        self.assertTrue(self.perm.has_permission(request, None))

    def test_denies_banned_user(self):
        u = User.objects.create_user(email="u2@ukma.edu.ua", password="x")
        u.is_banned = True
        request = self.factory.get("/")
        request.user = u
        self.assertFalse(self.perm.has_permission(request, None))
