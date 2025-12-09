from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models
from cloudinary_storage.storage import MediaCloudinaryStorage



class Year(models.Model):
    year = models.CharField()

    def __str__(self):
        return str(self.year)


class Gender(models.Model):
    gender = models.CharField(max_length=11)

    def __str__(self):
        return self.gender

# Custom manager for not using 'username' for login or registration
class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email обовʼязковий!')

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is False:
            raise ValueError('Суперюзер повинен мати is_staff=True')
        if extra_fields.get('is_superuser') is False:
            raise ValueError('Суперюзер повинен мати is_superuser=True')

        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    username = models.CharField(null=True, blank=True, unique=True)
    email = models.EmailField(unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    role = models.ForeignKey("auction.Role", on_delete=models.CASCADE, null=True, blank=True)
    gender = models.ForeignKey(Gender, on_delete=models.CASCADE, null=True, blank=True)    # questions
    faculty = models.ForeignKey("auction.Faculty", on_delete=models.CASCADE, null=True, blank=True)
    major = models.ForeignKey("auction.Major", on_delete=models.CASCADE, null=True, blank=True)
    year = models.ForeignKey(Year, on_delete=models.CASCADE, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    profile_pic = models.ImageField(upload_to='profile_pic/', null=True, blank=True)

    facebook = models.URLField(null=True, blank=True)
    instagram = models.URLField(null=True, blank=True)
    discord_id = models.CharField(null=True, blank=True)
    soundcloud = models.URLField(null=True, blank=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.username})"


class UserPhotos(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="user_photos")
    photo = models.ImageField(storage=MediaCloudinaryStorage(), upload_to='photos/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Photo of {self.user.username}"

