from django.urls import path

from . import auth

urlpatterns = [
    path("login", auth.LoginView.as_view(), name="auth-login"),
    path("refresh", auth.RefreshView.as_view(), name="auth-refresh"),
]
