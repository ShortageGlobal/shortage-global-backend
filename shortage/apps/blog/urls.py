from django.urls import include, path
from rest_framework import routers

from shortage.apps.blog.views import BlogPostViewSet

router = routers.DefaultRouter()

router.register(
    r"organizations/(?P<org_slug>[^/.]+)/blog",
    BlogPostViewSet,
    basename="blog",
)
