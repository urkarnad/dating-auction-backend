from django.contrib.auth.models import User
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


class Bid(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE) #who bets
    lot = models.ForeignKey(Lot, on_delete=models.CASCADE) #on who bets
    amount = models.IntegerField(default=0)


class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    text = models.TextField(null=True, blank=True)
    bid = models.ForeignKey(Bid, on_delete=models.CASCADE)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)
    lot = models.ForeignKey(Lot, on_delete=models.CASCADE)


class MyBids(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # who bet
    lot = models.ForeignKey(Lot, on_delete=models.CASCADE)  # on who bet
    bid = models.ForeignKey(Bid, on_delete=models.CASCADE)


class Themes(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Complaints(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    theme = models.ForeignKey(Themes, on_delete=models.CASCADE)
    text = models.TextField(null=True, blank=True)
