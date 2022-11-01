from django.urls import path
from .views import RegistrationView, ActivationView, ProfileView

urlpatterns = [
    path(r"users/register/", RegistrationView.as_view(), name="users_register"),
    path(r"users/activate/", ActivationView.as_view(), name="users_activate"),
    path(r"private/users/profile/", ProfileView.as_view(), name="users_profile"),
]
