"""
API urlpatterns
"""
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.views.generic import TemplateView
from shortage import settings

urlpatterns = [
    path("", include("shortage.apps.catalog.urls")),
    path("", include("shortage.apps.packages.urls")),
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
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
