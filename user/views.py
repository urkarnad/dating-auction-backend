from django.contrib.auth import logout
from django.http import JsonResponse
from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from DatingAuction import settings
import logging

from user.models import CustomUser
from user.serializers import RegisterSerializer, CustomUserSerializer, LoginSerializer

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

@csrf_exempt
@require_http_methods(["POST"])
def logout_view(request):
    logger.info(f"Logout attempt - User: {request.user}, Authenticated: {request.user.is_authenticated}")
    logger.info(f"Session key before logout: {request.session.session_key}")

    logout(request)

    logger.info(f"After logout - User: {request.user}, Authenticated: {request.user.is_authenticated}")
    logger.info(f"Session key after logout: {request.session.session_key}")

    return JsonResponse({
        'message': 'Successfully logged out',
        'redirect_url': f'{settings.FRONTEND_URL}/login'
    }, status=200)
    #return redirect(f'{settings.FRONTEND_URL}/login') # Where redirect

class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        logger.info(f'user: {user}')

        refresh = RefreshToken.for_user(user)

        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': CustomUserSerializer(user).data
        }, status=201)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']

        refresh = RefreshToken.for_user(user)

        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        })
