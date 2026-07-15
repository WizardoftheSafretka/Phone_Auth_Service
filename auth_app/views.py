from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from users.models import CustomUser
from .serializers import (
    PhoneNumberSerializer,
    VerifySerializer,
    ActivateInviteSerializer,
    RefreshSerializer,
    LogoutSerializer,
)
from .services import AuthService


# ============= WEB VIEWS =============

def login_view(request):
    if request.user.is_authenticated:
        return redirect('profile')

    if request.method == 'POST':
        phone_number = request.POST.get('phone_number')
        if phone_number:
            AuthService.send_verification_code(phone_number)
            request.session['phone_number'] = phone_number
            messages.success(request, 'Код авторизации отправлен!')
            return redirect('verify')
        else:
            messages.error(request, 'Введите номер телефона')

    return render(request, 'auth/login.html')


def verify_view(request):
    if request.user.is_authenticated:
        return redirect('profile')

    phone_number = request.session.get('phone_number')
    if not phone_number:
        messages.error(request, 'Сначала запросите код')
        return redirect('login')

    if request.method == 'POST':
        code = request.POST.get('code')
        success, message = AuthService.verify_code(phone_number, code)

        if success:
            user, created = AuthService.get_or_create_user(phone_number)
            user.is_verified = True
            user.save(update_fields=['is_verified'])
            login(request, user)
            messages.success(request, f'Добро пожаловать!')
            return redirect('profile')
        else:
            messages.error(request, message)

    return render(request, 'auth/verify.html', {'phone_number': phone_number})


@login_required
def profile_view(request):
    user = request.user

    if request.method == 'POST':
        invite_code = request.POST.get('invite_code')
        if invite_code:
            success, message = AuthService.activate_invite_code(user, invite_code)
            if success:
                messages.success(request, message)
            else:
                messages.error(request, message)
        return redirect('profile')

    profile = AuthService.get_user_profile(user)
    return render(request, 'users/profile.html', {'profile': profile})


@login_required
def logout_view(request):
    logout(request)
    messages.info(request, 'Вы вышли из системы')
    return redirect('login')


# ============= API VIEWS =============

class SendCodeView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        request_body=PhoneNumberSerializer,
        responses={200: 'Код отправлен', 400: 'Ошибка'}
    )
    def post(self, request):
        serializer = PhoneNumberSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone_number = serializer.validated_data['phone_number']
        AuthService.send_verification_code(phone_number)

        return Response({
            'message': 'Код авторизации отправлен',
            'phone_number': phone_number
        })


class VerifyCodeView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        request_body=VerifySerializer,
        responses={200: 'Успешно', 400: 'Ошибка'}
    )
    def post(self, request):
        serializer = VerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone_number = serializer.validated_data['phone_number']
        code = serializer.validated_data['code']

        success, message = AuthService.verify_code(phone_number, code)

        if not success:
            return Response({'error': message}, status=status.HTTP_400_BAD_REQUEST)

        user, created = AuthService.get_or_create_user(phone_number)
        user.is_verified = True
        user.save(update_fields=['is_verified'])

        refresh = RefreshToken.for_user(user)
        profile = AuthService.get_user_profile(user)

        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': profile
        })


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = AuthService.get_user_profile(request.user)
        return Response(profile)


class ActivateInviteView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=ActivateInviteSerializer,
        responses={200: 'Активирован', 400: 'Ошибка'}
    )
    def post(self, request):
        serializer = ActivateInviteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        success, message = AuthService.activate_invite_code(
            request.user,
            serializer.validated_data['invite_code']
        )

        if not success:
            return Response({'error': message}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'message': message})


class CustomTokenRefreshView(TokenRefreshView):
    pass


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            token = RefreshToken(serializer.validated_data['refresh'])
            token.blacklist()
            return Response({'message': 'Выход выполнен'})
        except Exception:
            return Response(
                {'error': 'Неверный токен'},
                status=status.HTTP_400_BAD_REQUEST
            )