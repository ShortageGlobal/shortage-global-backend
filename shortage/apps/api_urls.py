"""
API urlpatterns
"""
from django.urls import path, include
from django.views.generic import TemplateView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from shortage import settings

urlpatterns = [
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    path("", include("shortage.apps.catalog.urls")),
    path("", include("shortage.apps.packages.urls")),
    path("", include("shortage.apps.users.urls")),
]

if settings.DEBUG:
    urlpatterns.append(
        path(
            "swagger-ui/",
            TemplateView.as_view(
                template_name="swagger-ui.html",
            ),
            name="swagger-ui",
        ),
    )
