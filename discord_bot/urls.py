from django.urls import path
from auction import views

urlpatterns = [
    path("link-discord/", views.link_discord),
]