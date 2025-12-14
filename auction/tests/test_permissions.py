from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

from auction.models import Lot

User = get_user_model()


class AuctionPermissionsTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.user = User.objects.create_user(
            email="u@ukma.edu.ua",
            password="x",
            first_name="A",
            last_name="B",
        )
        self.banned = User.objects.create_user(
            email="b@ukma.edu.ua",
            password="x",
            first_name="C",
            last_name="D",
        )
        self.banned.is_banned = True
        self.banned.save(update_fields=["is_banned"])

        self.lot_owner = User.objects.create_user(
            email="owner@ukma.edu.ua",
            password="x",
            first_name="Owner",
            last_name="X",
        )
        self.lot = Lot.objects.create(user=self.lot_owner, last_bet=0)

    def test_banned_user_cannot_post_bid_or_comment_on_lot_detail(self):
        self.client.force_authenticate(user=self.banned)
        url = reverse("lot_detail", kwargs={"pk": self.lot.id})

        r1 = self.client.post(url, data={"amount": 10}, format="json")
        self.assertEqual(r1.status_code, 403)

        r2 = self.client.post(url, data={"text": "hi"}, format="json")
        self.assertEqual(r2.status_code, 403)

    def test_non_admin_cannot_delete_lot(self):
        self.client.force_authenticate(user=self.user)
        url = reverse("lot_detail", kwargs={"pk": self.lot.id})

        resp = self.client.delete(url)
        self.assertEqual(resp.status_code, 403)

    def test_admin_can_delete_lot(self):
        admin = User.objects.create_user(
            email="admin@ukma.edu.ua",
            password="x",
            first_name="Admin",
            last_name="Z",
        )
        admin.is_staff = True
        admin.is_superuser = True
        admin.save(update_fields=["is_staff", "is_superuser"])

        self.client.force_authenticate(user=admin)
        url = reverse("lot_detail", kwargs={"pk": self.lot.id})

        resp = self.client.delete(url)
        self.assertEqual(resp.status_code, 204)

        self.assertFalse(Lot.objects.filter(id=self.lot.id).exists())
