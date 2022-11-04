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
)

urlpatterns = [
    path(r"token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path(r"token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path(r"token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    path(r"users/register/", RegistrationView.as_view(), name="users_register"),
    path(r"users/activate/", ActivationView.as_view(), name="users_activate"),
    path(r"private/users/profile/", ProfileView.as_view(), name="users_profile"),
]
