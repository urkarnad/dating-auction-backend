from django.test import TestCase
from django.contrib.auth import get_user_model

from auction.models import Lot, Faculty, Major, Role
from user.models import Gender, Year

User = get_user_model()


class AuctionModelsTests(TestCase):
    def setUp(self):
        self.faculty = Faculty.objects.create(name="FI")
        self.major = Major.objects.create(name="CS", faculty=self.faculty)
        self.role = Role.objects.create(name="Student")
        self.gender = Gender.objects.create(gender="female")
        self.year = Year.objects.create(year="2")

        self.user = User.objects.create_user(
            email="u@ukma.edu.ua",
            password="x",
            first_name="Anna",
            last_name="K",
        )

    def test_lot_first_name_falls_back_to_user_first_name(self):
        lot = Lot.objects.create(user=self.user)
        self.assertEqual(lot.first_name, "Anna")

    def test_lot_last_name_falls_back_to_user_last_name(self):
        lot = Lot.objects.create(user=self.user)
        self.assertEqual(lot.last_name, "K")

    def test_lot_display_first_name_overrides_user_first_name(self):
        lot = Lot.objects.create(user=self.user, display_first_name="Display")
        self.assertEqual(lot.first_name, "Display")

    def test_lot_display_last_name_overrides_user_last_name(self):
        lot = Lot.objects.create(user=self.user, display_last_name="Surname")
        self.assertEqual(lot.last_name, "Surname")
