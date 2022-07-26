"""
API urlpatterns
"""
from django.urls import path, include

urlpatterns = [
    path("", include("shortage.apps.catalog.urls")),
    path("", include("shortage.apps.packages.urls")),
]
