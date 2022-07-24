"""
API urlpatterns
"""
from django.urls import path, include

urlpatterns = [
    path("", include("shortage.apps.catalog.urls")),
]
