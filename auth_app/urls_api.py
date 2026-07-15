from django.urls import path
from .views import (
    SendCodeView,
    VerifyCodeView,
    ProfileView,
    ActivateInviteView,
    CustomTokenRefreshView,
    LogoutView,
)

urlpatterns = [
    path('send-code/', SendCodeView.as_view(), name='api_send_code'),
    path('verify/', VerifyCodeView.as_view(), name='api_verify'),
    path('profile/', ProfileView.as_view(), name='api_profile'),
    path('activate-invite/', ActivateInviteView.as_view(), name='api_activate_invite'),
    path('refresh/', CustomTokenRefreshView.as_view(), name='api_refresh'),
    path('logout/', LogoutView.as_view(), name='api_logout'),
]