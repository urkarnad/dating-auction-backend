from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from user.views import logout_view, auth_success, RegisterView

urlpatterns = [
    path('auth/', include('social_django.urls', namespace='social')),
    path('auth/success/', auth_success, name='auth_success'),
    path('logout/', logout_view, name='logout'),
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', TokenObtainPairView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
