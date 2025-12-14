from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError

from user.serializers import RegisterSerializer, LoginSerializer, CustomUserSerializer
from user.models import Gender, Year
from auction.models import Role, Faculty, Major

User = get_user_model()


class RegisterSerializerTests(TestCase):
    def test_register_rejects_non_ukma_email(self):
        s = RegisterSerializer(data={
            "email": "test@gmail.com",
            "first_name": "A",
            "last_name": "B",
            "password": "12345qwerty",
            "confirm_password": "12345qwerty",
        })
        self.assertFalse(s.is_valid())
        self.assertIn("email", s.errors)

    def test_register_rejects_password_mismatch(self):
        s = RegisterSerializer(data={
            "email": "x@ukma.edu.ua",
            "first_name": "A",
            "last_name": "B",
            "password": "111",
            "confirm_password": "222",
        })
        self.assertFalse(s.is_valid())
        self.assertIn("non_field_errors", s.errors)

    def test_register_creates_user(self):
        s = RegisterSerializer(data={
            "email": "new@ukma.edu.ua",
            "first_name": "A",
            "last_name": "B",
            "password": "StrongPass123!",
            "confirm_password": "StrongPass123!",
        })
        self.assertTrue(s.is_valid(), s.errors)
        user = s.save()
        self.assertEqual(user.email, "new@ukma.edu.ua")
        self.assertTrue(user.check_password("StrongPass123!"))


class LoginSerializerTests(TestCase):
    def test_login_rejects_wrong_credentials(self):
        User.objects.create_user(email="u@ukma.edu.ua", password="Correct123!")
        s = LoginSerializer(data={"email": "u@ukma.edu.ua", "password": "Wrong"})
        self.assertFalse(s.is_valid())

    def test_login_accepts_correct_credentials(self):
        User.objects.create_user(email="u@ukma.edu.ua", password="Correct123!")
        s = LoginSerializer(data={"email": "u@ukma.edu.ua", "password": "Correct123!"})
        self.assertTrue(s.is_valid(), s.errors)
        self.assertIn("user", s.validated_data)


class CustomUserSerializerTests(TestCase):
    def setUp(self):
        self.role = Role.objects.create(name="Role1")
        self.gender = Gender.objects.create(gender="Female")
        self.faculty1 = Faculty.objects.create(name="F1")
        self.faculty2 = Faculty.objects.create(name="F2")
        self.major1 = Major.objects.create(name="M1", faculty=self.faculty1)
        self.year = Year.objects.create(year="1")

        self.user = User.objects.create_user(
            email="u@ukma.edu.ua", password="Correct123!",
            first_name="A", last_name="B"
        )

    def test_major_must_belong_to_faculty(self):
        # major from faculty1, but choose faculty2
        data = {
            "first_name": "A",
            "last_name": "B",
            "role": self.role.id,
            "gender": self.gender.id,
            "faculty": self.faculty2.id,
            "major": self.major1.id,
            "year": self.year.id,
        }
        s = CustomUserSerializer(instance=self.user, data=data, partial=True)
        self.assertFalse(s.is_valid())
        self.assertIn("non_field_errors", s.errors)
