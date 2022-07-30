from django.urls import include, path
from rest_framework import routers
from .views import PackageViewSet, PackageCreationViewSet

router = routers.DefaultRouter()

# Packages
router.register(
    r"organizations/(?P<org_slug>[^/.]+)/packages",
    PackageViewSet,
    basename="organization_package",
)
router.register(
    r"organizations/(?P<org_slug>[^/.]+)/packages",
    PackageCreationViewSet,
    basename="organization_package",
)

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    path("", include(router.urls)),
]
