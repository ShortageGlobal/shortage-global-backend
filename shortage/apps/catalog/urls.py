from django.urls import include, path
from rest_framework import routers
from .views import (
    PromotedOrganizationsViewSet,
    PromotedProductsViewSet,
    PromotedCategoriesViewSet,
    OrganizationViewSet,
    OrganizationInstructionsViewSet,
    OrganizationCategoriesViewSet,
    OrganizationProductsViewSet,
    OrganizationProductViewSet,
    OrganizationProductOnlineStoresViewSet,
)

router = routers.DefaultRouter()

# Promoted
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

# Organizations
router.register(r"organizations", OrganizationViewSet, basename="organizations")

# Instructions
router.register(
    r"organizations/(?P<org_slug>[^/.]+)/instructions",
    OrganizationInstructionsViewSet,
    basename="organization_instructions",
)

# Categories
router.register(
    r"organizations/(?P<org_slug>[^/.]+)/categories",
    OrganizationCategoriesViewSet,
    basename="organization_categories",
)

# Products
router.register(
    r"organizations/(?P<org_slug>[^/.]+)/products",
    OrganizationProductsViewSet,
    basename="organization_products",
)
router.register(
    r"organizations/(?P<org_slug>[^/.]+)/products",
    OrganizationProductViewSet,
    basename="organization_product",
)


# Online stores
router.register(
    r"organizations/(?P<org_slug>[^/.]+)/products/(?P<product_slug>[^/.]+)/online-stores",
    OrganizationProductOnlineStoresViewSet,
    basename="organization_product_online_stores",
)

# Packages

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    path("", include(router.urls)),
]
