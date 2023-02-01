from django.conf import settings
from rest_framework import viewsets, mixins, permissions, status, exceptions, status
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.schemas.openapi import AutoSchema
from rest_framework import exceptions
from shortage.apps.catalog.models import Product, Organization
from shortage.apps.catalog.private.serializers import (
    PrivateOrganizationReadSerializer,
    PrivateOrganizationWriteSerializer,
    PrivateProductSerializer,
)
from shortage.apps.catalog.exceptions import OneOrganizationPerUser
from shortage.helpers.permissions import IsObjectOwner


class PrivateOrganizationSlugExistsViewSet(viewsets.ViewSet):
    """
    Checks if organization with specified slug exists
    """

    schema = AutoSchema(
        tags=["Organizations"],
    )

    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "slug"

    def retrieve(self, request, slug):
        # check blacklist
        if slug in settings.ORGANIZATION_SLUG_BLACKLIST:
            return Response(status=status.HTTP_200_OK)

        # check existing organizations
        if Organization.objects.filter(slug=slug).exists():
            return Response(status=status.HTTP_200_OK)

        # slug not found, meaning it's safe to create
        raise exceptions.NotFound()


class PrivateOrganizationViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """Retrieve/create/update organization owned by a current user"""

    schema = AutoSchema(
        tags=["Private", "Organizations"],
    )

    permission_classes = [permissions.IsAuthenticated]
    paginator = None
    lookup_field = "slug"

    def get_serializer_class(self):
        if self.action == "create" or self.action == "update":
            return PrivateOrganizationWriteSerializer
        return PrivateOrganizationReadSerializer

    def get_queryset(self):
        if "retrieve" == self.action or "list" == self.action:
            return Organization.objects.active().filter(owner=self.request.user)
        else:
            # Prevent changes to organizations which you don't own and which are already verified
            return Organization.objects.filter(
                owner=self.request.user, is_verified=False
            )

    def create(self, request, *args, **kwargs):
        # Allow only one organization per user
        if Organization.objects.filter(owner=self.request.user).exists():
            raise OneOrganizationPerUser()

        # Todo: Send an email about organization's creation
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        # Todo: Send an email about changes to the organization
        return super().update(request, *args, **kwargs)


class PrivateProductsViewSet(viewsets.ModelViewSet):
    schema = AutoSchema(
        tags=["Private", "Products"],
    )

    permission_classes = [permissions.IsAuthenticated, IsObjectOwner]
    serializer_class = PrivateProductSerializer
    lookup_field = "slug"

    def __init__(self):
        self.organization = None

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

    def create(self, request, *args, **kwargs):
        self.organization = get_object_or_404(
            Organization.objects.public(), slug=self.kwargs["org_slug"]
        )

        return super().create(request, *args, **kwargs)

    def perform_destroy(self, instance):
        # Do a soft delete
        instance.is_deleted = True
        instance.save()


class PrivateProductsSlugExistsViewSet(viewsets.ViewSet):
    """
    Checks if a product with the specified slug belongs to the given organization
    """

    schema = AutoSchema(
        tags=["Private", "Products"],
    )

    permission_classes = [permissions.IsAuthenticated, IsObjectOwner]
    lookup_field = "slug"

    def retrieve(self, request, org_slug, slug):
        if Product.objects.filter(organization__slug=org_slug, slug=slug).exists():
            return Response(status=status.HTTP_200_OK)
        else:
            raise exceptions.NotFound()
