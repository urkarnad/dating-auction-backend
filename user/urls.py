from django.urls import path, include

from user.views import logout_view

urlpatterns = [
    path('auth/', include('social_django.urls', namespace='social')),
    path('logout/', logout_view, name='logout'),
]
