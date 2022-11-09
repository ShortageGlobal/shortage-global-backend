from django.urls import include, path
from rest_framework import routers

from shortage.apps.blog.image_upload import upload_image

router = routers.DefaultRouter()

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    path("", include(router.urls)),
    path("upload_image/", upload_image),
]
