from django.urls import path

from . import auth

urlpatterns = [
    path("login", auth.LoginView.as_view(), name="auth-login"),
    path("refresh", auth.RefreshView.as_view(), name="auth-refresh"),
    path(".well-known/jwks.json", auth.JwksView.as_view(), name="auth-jwks"),
]
