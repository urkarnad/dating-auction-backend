from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock

User = get_user_model()


class UserFunctionalTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_register_success_returns_tokens_and_user(self):
        url = reverse("register")
        resp = self.client.post(url, data={
            "email": "new@ukma.edu.ua",
            "first_name": "A",
            "last_name": "B",
            "password": "StrongPass123!",
            "confirm_password": "StrongPass123!",
        }, format="json")

        self.assertEqual(resp.status_code, 201)
        self.assertIn("access", resp.data)
        self.assertIn("refresh", resp.data)
        self.assertIn("user", resp.data)

        # CustomUserSerializer у вас НЕ повертає email, тому перевіряємо те, що є
        self.assertIn("id", resp.data["user"])
        self.assertEqual(resp.data["user"]["first_name"], "A")
        self.assertEqual(resp.data["user"]["last_name"], "B")

    def test_register_rejects_non_ukma_email(self):
        url = reverse("register")
        resp = self.client.post(url, data={
            "email": "new@gmail.com",
            "first_name": "A",
            "last_name": "B",
            "password": "StrongPass123!",
            "confirm_password": "StrongPass123!",
        }, format="json")

        self.assertEqual(resp.status_code, 400)
        self.assertIn("email", resp.data)

    def test_login_success_returns_access_and_refresh(self):
        User.objects.create_user(email="u@ukma.edu.ua", password="Correct123!")

        url = reverse("login") 
        resp = self.client.post(url, data={
            "email": "u@ukma.edu.ua",
            "password": "Correct123!",
        }, format="json")

        self.assertEqual(resp.status_code, 200)
        self.assertIn("access", resp.data)
        self.assertIn("refresh", resp.data)

    def test_login_wrong_password_returns_401(self):
        User.objects.create_user(email="u@ukma.edu.ua", password="Correct123!")

        url = reverse("login")
        resp = self.client.post(url, data={
            "email": "u@ukma.edu.ua",
            "password": "WRONG",
        }, format="json")

        self.assertEqual(resp.status_code, 401)
        self.assertIn("detail", resp.data)

    def test_token_refresh_returns_new_access(self):
        User.objects.create_user(email="u@ukma.edu.ua", password="Correct123!")

        login_url = reverse("login")
        login_resp = self.client.post(login_url, data={
            "email": "u@ukma.edu.ua",
            "password": "Correct123!",
        }, format="json")
        self.assertEqual(login_resp.status_code, 200)
        refresh = login_resp.data["refresh"]

        refresh_url = reverse("token_refresh")
        refresh_resp = self.client.post(refresh_url, data={
            "refresh": refresh
        }, format="json")

        self.assertEqual(refresh_resp.status_code, 200)
        self.assertIn("access", refresh_resp.data)

    def test_logout_returns_json_message(self):
        u = User.objects.create_user(email="u@ukma.edu.ua", password="Correct123!")
        self.client.force_login(u)

        url = reverse("logout")
        resp = self.client.post(url)

        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["message"], "Successfully logged out")
        self.assertIn("redirect_url", data)

    def test_auth_success_redirects_with_tokens_when_authenticated(self):
        u = User.objects.create_user(email="u@ukma.edu.ua", password="Correct123!")
        self.client.force_login(u)

        mock_refresh = MagicMock()
        mock_refresh.access_token = "ACCESS"
        mock_refresh.__str__.return_value = "REFRESH"

        with patch("user.views.settings.FRONTEND_URL", "http://frontend.test"), \
             patch("user.views.RefreshToken.for_user", return_value=mock_refresh):
            resp = self.client.get(reverse("auth_success"))

        self.assertEqual(resp.status_code, 302)
        location = resp["Location"]
        self.assertTrue(location.startswith("http://frontend.test/auth/callback"))
        self.assertIn("access_token=ACCESS", location)
        self.assertIn("refresh_token=REFRESH", location)

    def test_auth_success_redirects_to_login_when_not_authenticated(self):
        with patch("user.views.settings.FRONTEND_URL", "http://frontend.test"):
            resp = self.client.get(reverse("auth_success"))

        self.assertEqual(resp.status_code, 302)
        self.assertTrue(resp["Location"].startswith("http://frontend.test/login"))
        self.assertIn("error=auth_failed", resp["Location"])
