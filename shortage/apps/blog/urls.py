from django.urls import include, path
from rest_framework import routers

from shortage.apps.blog.views import upload_image, ShortageBlogPostViewSet

router = routers.DefaultRouter()

router.register(
    r"blog_posts",
    ShortageBlogPostViewSet,
    basename="shortage_blog_posts",
)

# Wire up our API using automatic URL routing.
urlpatterns = [
    path("", include(router.urls)),
    path("private/upload_image/", upload_image),
]
