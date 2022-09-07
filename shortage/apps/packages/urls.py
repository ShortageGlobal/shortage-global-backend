from django.urls import include, path
from rest_framework import routers
from .views import PackageViewSet, CartViewSet, CartItemViewSet

router = routers.DefaultRouter()

# Packages
router.register(
    r"organizations/(?P<org_slug>[^/.]+)/packages",
    PackageViewSet,
    basename="organization_package",
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

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    path("", include(router.urls)),
]
