from django.contrib.auth import logout
from django.shortcuts import redirect
from rest_framework_simplejwt.tokens import RefreshToken
from DatingAuction import settings
import logging

logger = logging.getLogger(__name__)


def auth_success(request):
    logger.info(f"auth_success called")
    logger.info(f"User: {request.user}")
    logger.info(f"Is authenticated: {request.user.is_authenticated}")

    user = request.user

    if not user.is_authenticated:
        logger.error(f"User not authenticated, redirecting to login")
        return redirect(f'{settings.FRONTEND_URL}/login?error=auth_failed')

    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)
    refresh_token = str(refresh)

    logger.info(f"Tokens created for user {user.username}")

    frontend_callback_url = (
        f"{settings.FRONTEND_URL}/auth/callback"
        f"?access_token={access_token}"
        f"&refresh_token={refresh_token}"
    )

    logger.info(f"redirecting to: {frontend_callback_url}")

    return redirect(frontend_callback_url)


def logout_view(request):
    logout(request)
    return redirect(f'{settings.FRONTEND_URL}/login') # Where redirect
