from django.urls import path
from .views import login_view, verify_view, profile_view, logout_view

urlpatterns = [
    path('', login_view, name='login'),
    path('verify/', verify_view, name='verify'),
    path('profile/', profile_view, name='profile'),
    path('logout/', logout_view, name='logout'),
]