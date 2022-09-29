from django.urls import include, path
from rest_framework import routers

from .private.views import PrivateOrganizationPackagesViewSet
from .views import (
    PackageViewSet,
    PackageCreationViewSet,
    CartViewSet,
    CartItemViewSet,
    CorporateDonationsViewSet,
)

router = routers.DefaultRouter()

# Packages
router.register(
    r"organizations/(?P<org_slug>[^/.]+)/packages",
    PackageViewSet,
    basename="organization_packages",
)
router.register(
    r"organizations/(?P<org_slug>[^/.]+)/packages",
    PackageCreationViewSet,
    basename="organization_packages",
)
router.register(
    r"private/organizations/(?P<org_slug>[^/.]+)/packages",
    PrivateOrganizationPackagesViewSet,
    basename="private_organization_packages",
)
# Cart
router.register(
    r"carts",
    CartViewSet,
    basename="cart",
)
router.register(
    r"carts/(?P<cart_pk>[^/.]+)/items",
    CartItemViewSet,
    basename="cart_item",
)

# Corporate Donations
router.register(
    r"corporate-donations",
    CorporateDonationsViewSet,
    basename="corporate-donations",
)

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    path("", include(router.urls)),
]
