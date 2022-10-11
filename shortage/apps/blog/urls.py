from django.urls import include, path
from rest_framework import routers

from shortage.apps.blog.views import BlogPostViewSet

router = routers.DefaultRouter()

router.register(
    r"organizations/(?P<org_slug>[^/.]+)/blog",
    BlogPostViewSet,
    basename="blog",
)

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    path("", include(router.urls)),
]
