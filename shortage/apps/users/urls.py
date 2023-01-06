from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from .views import (
    RegistrationView,
    ActivationView,
    ProfileView,
    RequestPasswordResetView,
    CheckPasswordResetTokenView,
    ConfirmResetPasswordView,
)

urlpatterns = [
    path(r"token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path(r"token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path(r"token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    path(r"users/register/", RegistrationView.as_view(), name="users_register"),
    path(r"users/activate/", ActivationView.as_view(), name="users_activate"),
    path(r"private/users/profile/", ProfileView.as_view(), name="users_profile"),
    path(
        r"users/reset_password/",
        RequestPasswordResetView.as_view(),
        name="reset_password",
    ),
    path(
        r"users/check_reset_password_token/",
        CheckPasswordResetTokenView.as_view(),
        name="check_reset_password_token",
    ),
    path(
        r"users/confirm_reset_password/",
        ConfirmResetPasswordView.as_view(),
        name="confirm_reset_password",
    ),
]
