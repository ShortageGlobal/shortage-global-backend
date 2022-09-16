from django.urls import include, path
from rest_framework import routers
from .views import (
    PromotedOrganizationsViewSet,
    PromotedProductsViewSet,
    PromotedCategoriesViewSet,
    OrganizationViewSet,
    InstructionsViewSet,
    CategoriesViewSet,
    ProductsViewSet,
    ProductViewSet,
    OnlineStoresViewSet,
    PrivateOrganizationViewSet,
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

# Organization
router.register(r"organizations", OrganizationViewSet, basename="organization")
router.register(
    r"private/organizations",
    PrivateOrganizationViewSet,
    basename="private_organization",
)


# Instructions
router.register(
    r"organizations/(?P<org_slug>[^/.]+)/instructions",
    InstructionsViewSet,
    basename="instructions",
)

# Categories
router.register(
    r"organizations/(?P<org_slug>[^/.]+)/categories",
    CategoriesViewSet,
    basename="categories",
)

# Products
router.register(
    r"organizations/(?P<org_slug>[^/.]+)/products",
    ProductsViewSet,
    basename="products",
)
router.register(
    r"organizations/(?P<org_slug>[^/.]+)/products",
    ProductViewSet,
    basename="product",
)


# Online stores
router.register(
    r"organizations/(?P<org_slug>[^/.]+)/products/(?P<product_slug>[^/.]+)/online-stores",
    OnlineStoresViewSet,
    basename="online_stores",
)

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    path("", include(router.urls)),
]
