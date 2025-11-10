from django.db import models


class Year(models.Model):
    year = models.CharField()

    def __str__(self):
        return str(self.year)


class Gender(models.Model):
    gender = models.CharField(max_length=11)

    def __str__(self):
        return self.gender


class CustomUser(models.Model):
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    role = models.ForeignKey("auction.Role", on_delete=models.CASCADE)
    gender = models.ForeignKey(Gender, on_delete=models.CASCADE) #questions
    faculty = models.ForeignKey("auction.Faculty", on_delete=models.CASCADE)
    major = models.ForeignKey("auction.Major", on_delete=models.CASCADE, null=True, blank=True)
    year = models.ForeignKey(Year, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    profile_pic = models.ImageField(upload_to='profile_pic', null=True, blank=True)
    photo = models.ImageField(null=True, blank=True)
    facebook = models.URLField(null=True, blank=True)
    instagram = models.URLField(null=True, blank=True)
    discord = models.URLField(null=True, blank=True)
    soundcloud = models.URLField(null=True, blank=True)
