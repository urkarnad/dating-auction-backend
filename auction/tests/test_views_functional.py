from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from unittest.mock import patch

from auction.models import Lot, Bid, Comment

User = get_user_model()


class AuctionFunctionalTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(email="u@ukma.edu.ua", password="x", first_name="A", last_name="B")
        self.other = User.objects.create_user(email="v@ukma.edu.ua", password="x", first_name="C", last_name="D")

    def auth(self, user):
        self.client.force_authenticate(user=user)

    def test_homepage_returns_paginated_list(self):
        Lot.objects.create(user=self.user, last_bet=0)
        Lot.objects.create(user=self.other, last_bet=10)

        self.auth(self.user)
        url = reverse("homepage")
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)
        self.assertIn("results", resp.data)

    def test_create_mylot_only_once(self):
        self.auth(self.user)
        url = reverse("my_lot")

        r1 = self.client.post(url, data={}, format="json")
        self.assertEqual(r1.status_code, 201)

        r2 = self.client.post(url, data={}, format="json")
        self.assertEqual(r2.status_code, 400)
        self.assertIn("detail", r2.data)

    def test_create_mylot_denied_when_banned(self):
        self.user.is_banned = True
        self.user.save(update_fields=["is_banned"])

        self.auth(self.user)
        url = reverse("my_lot")
        resp = self.client.post(url, data={}, format="json")

        self.assertEqual(resp.status_code, 403)

    def test_get_mylot_404_if_missing(self):
        self.auth(self.user)
        url = reverse("my_lot")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)

    def test_lot_detail_get(self):
        lot = Lot.objects.create(user=self.other, last_bet=0)

        self.auth(self.user)
        url = reverse("lot_detail", kwargs={"pk": lot.id})
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["id"], lot.id)

    def test_place_bid_updates_last_bet_and_overbid_flags(self):
        lot = Lot.objects.create(user=self.other, last_bet=0)

        prev_bid = Bid.objects.create(user=self.user, lot=lot, amount=10, is_overbid=False)
        lot.last_bet = 10
        lot.save(update_fields=["last_bet"])

        self.auth(self.other)  
        url = reverse("lot_detail", kwargs={"pk": lot.id})

        with patch("auction.views.notification_service.notify_bid_overbid_sync") as notify_mock:
            resp = self.client.post(url, data={"amount": 20, "text": "my bid"}, format="json")

        self.assertEqual(resp.status_code, 201)
        lot.refresh_from_db()
        self.assertEqual(lot.last_bet, 20)

        prev_bid.refresh_from_db()
        self.assertTrue(prev_bid.is_overbid)

        new_bid = Bid.objects.filter(lot=lot).order_by("-amount").first()
        self.assertIsNotNone(new_bid)
        self.assertFalse(new_bid.is_overbid)

        notify_mock.assert_called()

    def test_place_bid_rejected_if_too_small(self):
        lot = Lot.objects.create(user=self.other, last_bet=50)

        self.auth(self.user)
        url = reverse("lot_detail", kwargs={"pk": lot.id})
        resp = self.client.post(url, data={"amount": 55}, format="json")

        self.assertEqual(resp.status_code, 400)

    def test_add_comment_to_lot(self):
        lot = Lot.objects.create(user=self.other, last_bet=0)

        self.auth(self.user)
        url = reverse("lot_detail", kwargs={"pk": lot.id})
        resp = self.client.post(url, data={"text": "hello"}, format="json")

        self.assertEqual(resp.status_code, 201)
        self.assertTrue(Comment.objects.filter(lot=lot, user=self.user, text="hello").exists())
