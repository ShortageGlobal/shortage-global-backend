from django.urls import include, path
from rest_framework import routers
from .views import (
    PromotedOrganizationsViewSet,
    PromotedProductsViewSet,
    PromotedCategoriesViewSet,
)

router = routers.DefaultRouter()
router.register(
    r"promoted/organizations",
    PromotedOrganizationsViewSet,
    basename="promoted_organizations",
)
router.register(
    r"promoted/products", PromotedProductsViewSet, basename="promoted_products"
)
router.register(
    r"promoted/categories", PromotedCategoriesViewSet, basename="promoted_categories"
)

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    path("", include(router.urls)),
]
