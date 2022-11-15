"""
API urlpatterns
"""
from django.urls import path, include
from django.views.generic import TemplateView
from shortage import settings

urlpatterns = [
    path("", include("shortage.apps.users.urls")),
    path("", include("shortage.apps.catalog.urls")),
    path("", include("shortage.apps.packages.urls")),
    path("", include("shortage.apps.blog.urls")),
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
