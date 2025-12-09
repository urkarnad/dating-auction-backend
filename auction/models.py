from django.db import models

from user.models import CustomUser


class Role(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Faculty(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Major(models.Model):
    name = models.CharField(max_length=100)
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class Lot(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    description = models.TextField(null=True, blank=True)
    last_bet = models.IntegerField(default=0)
    display_first_name = models.CharField(max_length=150, blank=True)
    display_last_name = models.CharField(max_length=150, blank=True)

    @property
    def first_name(self):
        return self.display_first_name or self.user.first_name

    @property
    def last_name(self):
        return self.display_last_name or self.user.last_name


class Bid(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    lot = models.ForeignKey(Lot, on_delete=models.CASCADE)
    amount = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    is_overbid = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']


class Comment(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    text = models.TextField(null=True, blank=True)
    bid = models.ForeignKey(Bid, on_delete=models.CASCADE, null=True, blank=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)
    lot = models.ForeignKey(Lot, on_delete=models.CASCADE)

    class Meta:
        ordering = ['created_at']


class Themes(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Complaints(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    theme = models.ForeignKey(Themes, on_delete=models.CASCADE)
    text = models.TextField(null=True, blank=True)
