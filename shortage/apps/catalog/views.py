from rest_framework import viewsets, views, mixins, response
from .models import Organization, Product
from .serializers import (
    PromotedOrganizationPreviewSerializer,
    ProductPreviewSerializer,
    CategorySerializer,
)


class PromotedOrganizationsViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """The list of promoted organizations."""

    queryset = Organization.promoted_objects.all().order_by("-created_at")
    serializer_class = PromotedOrganizationPreviewSerializer


class PromotedProductsViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """The list of promoted products."""

    queryset = Product.promoted_objects.all().order_by("-created_at")
    serializer_class = ProductPreviewSerializer


class PromotedCategoriesViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """The list of categories for promoted products."""

    queryset = Product.promoted_objects.distinct("category").values_list(
        "category", flat=True
    )
    serializer_class = CategorySerializer
    paginator = None
