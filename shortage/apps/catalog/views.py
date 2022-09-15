from rest_framework import viewsets, mixins, filters, permissions
from django.shortcuts import get_object_or_404
from .models import Organization, Instruction, Product, OnlineStore
from .serializers import (
    OrganizationPreviewSerializer,
    InstructionSerializer,
    PromotedProductPreviewSerializer,
    ProductPreviewSerializer,
    CategorySerializer,
    OrganizationSerializer,
    ProductSerializer,
    OnlineStoreSerializer,
    PrivateOrganizationSerializer,
)


class PromotedOrganizationsViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """A list of promoted organizations"""

    queryset = Organization.objects.promoted().order_by("-created_at")
    serializer_class = OrganizationPreviewSerializer


class PromotedProductsViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """A list of promoted products"""

    serializer_class = PromotedProductPreviewSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name"]
    ordering = ["-top_priority", "position", "-created_at"]

    def get_queryset(self):
        queryset = Product.objects.promoted()

        # filter by category
        category = self.request.query_params.get("category")
        if category:
            queryset = queryset.filter(category=category)

        return queryset


class PromotedCategoriesViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """A list of categories of promoted products"""

    queryset = (
        Product.objects.promoted()
        .distinct("category")
        .values_list("category", flat=True)
    )
    serializer_class = CategorySerializer
    paginator = None


class OrganizationViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """Organization details"""

    queryset = Organization.objects.public()
    serializer_class = OrganizationSerializer
    lookup_field = "slug"


class PrivateOrganizationCreateViewSet(
    mixins.CreateModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet
):
    queryset = Organization.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PrivateOrganizationSerializer
    lookup_field = "slug"

    def create(self, request, *args, **kwargs):
        # Todo: Send an email about organization's creation
        return super().create(request, *args, **kwargs)


class PrivateOrganizationUpdateViewSet(
    mixins.UpdateModelMixin, viewsets.GenericViewSet
):

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PrivateOrganizationSerializer
    lookup_field = "slug"

    def get_queryset(self):
        return Organization.objects.all().filter(owner=self.request.user)

    def update(self, request, *args, **kwargs):
        # Todo: Send an email about changes to the organization
        return super().update(request, *args, **kwargs)


class InstructionsViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """A list of instructions that belong to the given organization"""

    serializer_class = InstructionSerializer
    paginator = None

    def get_queryset(self):
        organization = get_object_or_404(
            Organization.objects.public(), slug=self.kwargs["org_slug"]
        )
        return Instruction.objects.filter(organization=organization)


class ProductsViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """A list of products that belong to the given organization"""

    serializer_class = ProductPreviewSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name"]
    ordering = ["-top_priority", "position", "-created_at"]

    def get_queryset(self):
        organization = get_object_or_404(
            Organization.objects.public(), slug=self.kwargs["org_slug"]
        )
        queryset = Product.objects.filter(organization=organization)

        # filter by category
        category = self.request.query_params.get("category")
        if category:
            queryset = queryset.filter(category=category)

        return queryset


class CategoriesViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """A list of categories of the given organization's products"""

    serializer_class = CategorySerializer
    paginator = None

    def get_queryset(self):
        organization = get_object_or_404(
            Organization.objects.public(), slug=self.kwargs["org_slug"]
        )
        return (
            Product.objects.filter(organization=organization)
            .distinct("category")
            .values_list("category", flat=True)
        )


class ProductViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """Product details for the given slug and the given organization"""

    serializer_class = ProductSerializer
    lookup_field = "slug"

    def get_queryset(self):
        organization = get_object_or_404(
            Organization.objects.public(), slug=self.kwargs["org_slug"]
        )
        return Product.objects.filter(organization=organization)


class OnlineStoresViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    A list of online stores that belong to the given product of the given organization
    """

    serializer_class = OnlineStoreSerializer
    paginator = None

    def get_queryset(self):
        product = get_object_or_404(
            Product,
            slug=self.kwargs["product_slug"],
            organization__slug=self.kwargs["org_slug"],
        )
        return OnlineStore.objects.filter(product=product)
