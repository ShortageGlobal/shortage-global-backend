import logging

from rest_framework import viewsets, mixins, filters, permissions, status
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.schemas.openapi import AutoSchema

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
    ProductOrganizationPreviewSerializer,
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
    """Returns information about specific organization if that organization was verified"""

    schema = AutoSchema(
        tags=["Organizations"],
    )

    queryset = Organization.objects.public()
    serializer_class = OrganizationSerializer
    lookup_field = "slug"


class PrivateOrganizationSlugExistsView(
    mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    """
    Checks if organization with specified slug exists
    """

    schema = AutoSchema(
        tags=["Organizations"],
    )

    permission_classes = [permissions.IsAuthenticated]
    # Serializer class is needed because otherwise some stuff like schema generation won't work
    serializer_class = ProductOrganizationPreviewSerializer
    lookup_field = "slug"

    def get_queryset(self):
        return Organization.objects.all().filter(slug=self.kwargs[self.lookup_field])

    def retrieve(self, request, *args, **kwargs):
        if self.filter_queryset(self.get_queryset()).exists():
            return Response(status=status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_404_NOT_FOUND)


class PrivateOrganizationViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):

    schema = AutoSchema(
        tags=["Private", "Organizations"],
    )

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PrivateOrganizationSerializer
    lookup_field = "slug"

    def get_queryset(self):
        if "retrieve" == self.action or "list" == self.action:
            return Organization.objects.active().filter(owner=self.request.user)
        else:
            # Prevent changes to organizations which you don't own and which are already verified
            return Organization.objects.all().filter(
                owner=self.request.user, is_verified=False
            )

    """Allows you to create or update an organization. Only one organization is allowed per user"""

    def create(self, request, *args, **kwargs):

        # Allow only one organization per user
        if Organization.objects.all().filter(owner=self.request.user).exists():
            return Response(status=status.HTTP_409_CONFLICT)

        # Todo: Send an email about organization's creation
        return super().create(request, *args, **kwargs)

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


class PrivateProductsSlugExistsView(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """
    Checks if product with specified slug exists
    """

    schema = AutoSchema(
        tags=["Products"],
    )

    permission_classes = [permissions.IsAuthenticated]
    # Serializer class is needed because otherwise some stuff like schema generation won't work
    serializer_class = ProductPreviewSerializer
    lookup_field = "slug"

    def get_queryset(self):
        return Product.objects.all().filter(
            slug=self.kwargs[self.lookup_field],
            organization__slug=self.kwargs["org_slug"],
        )

    def retrieve(self, request, *args, **kwargs):
        if self.filter_queryset(self.get_queryset()).exists():
            return Response(status=status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_404_NOT_FOUND)


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
