from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError

from django.utils import timezone

from auction.models import Lot, Bid, Comment, Faculty, Major
from auction.serializers import BidSerializer, CommentSerializer

User = get_user_model()


class BidSerializerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="u@ukma.edu.ua", password="x", first_name="A", last_name="B")
        self.lot = Lot.objects.create(user=self.user, last_bet=50)

    def test_bid_amount_must_be_positive(self):
        s = BidSerializer(data={"user": self.user.id, "lot": self.lot.id, "amount": 0})
        self.assertFalse(s.is_valid())
        self.assertIn("amount", s.errors)

    def test_bid_must_be_at_least_last_bet_plus_10(self):
        # last_bet=50 -> мінімум 60
        s = BidSerializer(data={"user": self.user.id, "lot": self.lot.id, "amount": 59})
        self.assertFalse(s.is_valid())
        self.assertIn("non_field_errors", s.errors)

    def test_bid_ok_when_amount_is_minimum(self):
        s = BidSerializer(data={"user": self.user.id, "lot": self.lot.id, "amount": 60})
        self.assertTrue(s.is_valid(), s.errors)


class CommentSerializerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="u@ukma.edu.ua", password="x", first_name="A", last_name="B")
        self.other = User.objects.create_user(email="v@ukma.edu.ua", password="x", first_name="C", last_name="D")
        self.lot = Lot.objects.create(user=self.user, last_bet=0)
        self.other_lot = Lot.objects.create(user=self.other, last_bet=0)

        self.bid_on_other_lot = Bid.objects.create(user=self.other, lot=self.other_lot, amount=10)

    def test_comment_requires_text_or_bid(self):
        s = CommentSerializer(data={"user": self.user.id, "lot": self.lot.id})
        self.assertFalse(s.is_valid())
        self.assertIn("non_field_errors", s.errors)

    def test_comment_bid_must_belong_to_lot(self):
        # bid належить іншому лоту -> має впасти
        s = CommentSerializer(data={
            "user": self.user.id,
            "lot": self.lot.id,
            "bid": self.bid_on_other_lot.id,
            "text": "hi"
        })
        self.assertFalse(s.is_valid())
        self.assertIn("non_field_errors", s.errors)

    def test_comment_parent_must_belong_to_same_lot(self):
        parent = Comment.objects.create(user=self.other, lot=self.other_lot, text="parent")
        s = CommentSerializer(data={
            "user": self.user.id,
            "lot": self.lot.id,
            "parent": parent.id,
            "text": "reply"
        })
        self.assertFalse(s.is_valid())
        self.assertIn("non_field_errors", s.errors)

    def test_comment_antispam_rate_limit(self):
        # ANTI_SPAM_MAX = 5 per 1 minute
        for i in range(5):
            Comment.objects.create(user=self.user, lot=self.lot, text=f"c{i}")

        s = CommentSerializer(data={"user": self.user.id, "lot": self.lot.id, "text": "one more"})
        self.assertFalse(s.is_valid())
        self.assertIn("non_field_errors", s.errors)
