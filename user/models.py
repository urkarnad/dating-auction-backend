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


class CustomUser(AbstractUser):
    # built in: username, first_name, last_name, email
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

