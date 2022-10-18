from django.urls import include, path
from rest_framework import routers

from shortage.apps.blog.image_upload import upload_image
from shortage.apps.blog.views import PrivateBlogPostViewSet, RelatedBlogPostsViewSet

router = routers.DefaultRouter()

router.register(
    r"private/organizations/(?P<org_slug>[^/.]+)/blog",
    PrivateBlogPostViewSet,
    basename="blog",
)

router.register(
    r"organizations/(?P<org_slug>[^/.]+)/blog/packages/",
    RelatedBlogPostsViewSet,
    basename="blog",
)

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    path("", include(router.urls)),
    path("upload_image/", upload_image),
]
