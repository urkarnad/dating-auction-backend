from django.urls import path, include

from user.views import logout_view, auth_success

urlpatterns = [
    path('auth/', include('social_django.urls', namespace='social')),
    path('auth/success/', auth_success, name='auth_success'),
    path('logout/', logout_view, name='logout'),
]
