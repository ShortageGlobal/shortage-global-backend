from django.urls import include, path
from rest_framework import routers
from .views import (
    PromotedOrganizationsViewSet,
    PromotedExternalOrganizationsViewSet,
    PromotedProductsViewSet,
    PromotedCategoriesViewSet,
    PromotedOrganizationBlogPostsViewSet,
    OrganizationViewSet,
    InstructionsViewSet,
    CategoriesViewSet,
    ProductsViewSet,
    ProductViewSet,
    OrganizationBlogPostsViewSet,
    PrivateOrganizationViewSet,
    PrivateOrganizationSlugExistsViewSet,
    OrganizationRegistrationRequestViewSet,
    SitemapViewSet,
)
from .private.views import PrivateProductsSlugExistsViewSet, PrivateProductsViewSet

router = routers.DefaultRouter()

# Promoted
router.register(
    r"promoted/organizations",
    PromotedOrganizationsViewSet,
    basename="promoted_organizations",
)
router.register(
    r"promoted/external_organizations",
    PromotedExternalOrganizationsViewSet,
    basename="promoted_external_organizations",
)
router.register(
    r"promoted/products", PromotedProductsViewSet, basename="promoted_products"
)
router.register(
    r"promoted/categories", PromotedCategoriesViewSet, basename="promoted_categories"
)
router.register(
    r"promoted/blog_posts",
    PromotedOrganizationBlogPostsViewSet,
    basename="promoted_blog_posts",
)

# Organization
router.register(r"organizations", OrganizationViewSet, basename="organization")
router.register(
    r"private/exists/organizations",
    PrivateOrganizationSlugExistsViewSet,
    basename="private_exists_organization",
)
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
router.register(
    r"private/organizations/(?P<org_slug>[^/.]+)/products",
    PrivateProductsViewSet,
    basename="private_products",
)
router.register(
    r"private/exists/organizations/(?P<org_slug>[^/.]+)/products",
    PrivateProductsSlugExistsViewSet,
    basename="private_exists_products",
)

# Products
router.register(
    r"organizations/(?P<org_slug>[^/.]+)/blog_posts",
    OrganizationBlogPostsViewSet,
    basename="blog_posts",
)

# Request for nonprofits
router.register(
    r"register-nonprofit",
    OrganizationRegistrationRequestViewSet,
    basename="register_nonprofit",
)

# Sitemap routes
router.register(
    r"sitemap",
    SitemapViewSet,
    basename="sitemap",
)

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    path("", include(router.urls)),
]
