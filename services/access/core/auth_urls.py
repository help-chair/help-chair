from django.urls import path

from . import account, activation, auth, catalog, users

urlpatterns = [
    path("login", auth.LoginView.as_view(), name="auth-login"),
    path("refresh", auth.RefreshView.as_view(), name="auth-refresh"),
    path("logout", auth.LogoutView.as_view(), name="auth-logout"),
    path("activate", activation.ActivateView.as_view(), name="cuenta-activate"),
    path("me", account.CurrentUserView.as_view(), name="cuenta-me"),
    path(
        "me/onboarding",
        account.OnboardingView.as_view(),
        name="cuenta-onboarding",
    ),
    path("roles", catalog.RoleListView.as_view(), name="catalogo-roles"),
    path(
        "departamentos",
        catalog.DepartmentsView.as_view(),
        name="catalogo-departamentos",
    ),
    path("usuarios", users.UserListCreateView.as_view(), name="usuarios-lista"),
    path("usuarios/<uuid:id>", users.UserDetailView.as_view(), name="usuarios-detalle"),
    path(
        "usuarios/<uuid:id>/desbloquear",
        users.UserUnlockView.as_view(),
        name="usuarios-desbloquear",
    ),
    path(".well-known/jwks.json", auth.JwksView.as_view(), name="auth-jwks"),
]
