import re
import requests
from django.conf import settings
from rest_framework import (
    viewsets,
    mixins,
    filters,
    permissions,
    status,
    generics,
)
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.schemas.openapi import AutoSchema
from rest_framework import exceptions
from shortage.apps.catalog.models import (
    Product,
    Organization,
    Instruction,
    OrganizationBlogPost,
)
from shortage.apps.catalog.private.serializers import (
    PrivateOrganizationReadSerializer,
    PrivateOrganizationWriteSerializer,
    PrivateProductReadSerializer,
    PrivateProductWriteSerializer,
    PrivateInstructionSerializer,
    PrivateOrganizationBlogPostReadSerializer,
    PrivateOrganizationBlogPostWriteSerializer,
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
        if self.action in ["create", "update", "partial_update"]:
            return PrivateOrganizationWriteSerializer
        return PrivateOrganizationReadSerializer

    def get_queryset(self):
        if self.action == "retrieve" or self.action == "list":
            return (
                Organization.objects.active()
                .filter(owner=self.request.user)
                .order_by("-created_at")
            )
        else:
            # Prevent changes to organizations which you don't own and which are already verified
            return Organization.objects.active().filter(
                owner=self.request.user, is_verified=False
            )

    def create(self, request, *args, **kwargs):
        # Allow only one organization per user
        if Organization.objects.active().filter(owner=self.request.user).exists():
            raise OneOrganizationPerUser()

        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        # Todo: Send an email about changes to the organization
        return super().update(request, *args, **kwargs)


class PrivateProductsViewSet(viewsets.ModelViewSet):
    schema = AutoSchema(
        tags=["Private", "Products"],
    )

    permission_classes = [permissions.IsAuthenticated, IsObjectOwner]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name"]
    ordering = ["-created_at"]

    def __init__(self, **kwargs):
        self.organization = None
        super().__init__(**kwargs)

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return PrivateProductWriteSerializer
        return PrivateProductReadSerializer

    def get_queryset(self):
        self.organization = get_object_or_404(
            Organization.objects.active(), slug=self.kwargs["org_slug"]
        )
        queryset = Product.objects.active().filter(organization=self.organization)

        # filter by category
        category = self.request.query_params.get("category")
        if category:
            queryset = queryset.filter(category=category)

        return queryset

    def create(self, request, *args, **kwargs):
        self.organization = get_object_or_404(
            Organization.objects.active(), slug=self.kwargs["org_slug"]
        )

        return super().create(request, *args, **kwargs)

    def perform_destroy(self, instance):
        if self.organization.is_draft:
            # If organization hasn't been published, delete product entirely
            return super().perform_destroy(instance)

        # Do a soft delete if the organization has already been published
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


class PrivateInstructionsViewSet(viewsets.ModelViewSet):
    schema = AutoSchema(
        tags=["Private", "Instructions"],
    )

    permission_classes = [permissions.IsAuthenticated, IsObjectOwner]
    serializer_class = PrivateInstructionSerializer
    paginator = None

    def __init__(self, **kwargs):
        self.organization = None
        super().__init__(**kwargs)

    def get_queryset(self):
        organization = get_object_or_404(
            Organization.objects.active(), slug=self.kwargs["org_slug"]
        )
        return Instruction.objects.filter(organization=organization)

    def create(self, request, *args, **kwargs):
        self.organization = get_object_or_404(
            Organization.objects.active(), slug=self.kwargs["org_slug"]
        )

        return super().create(request, *args, **kwargs)


class PrivateOrganizationBlogPostsViewSet(viewsets.ModelViewSet):
    schema = AutoSchema(
        tags=["Private", "Blog"],
    )

    permission_classes = [permissions.IsAuthenticated, IsObjectOwner]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["title"]
    ordering = ["-created_at"]

    def __init__(self, **kwargs):
        self.organization = None
        super().__init__(**kwargs)

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return PrivateOrganizationBlogPostWriteSerializer
        return PrivateOrganizationBlogPostReadSerializer

    def get_queryset(self):
        self.organization = get_object_or_404(
            Organization.objects.active(), slug=self.kwargs["org_slug"]
        )
        queryset = OrganizationBlogPost.objects.active().filter(
            organization=self.organization
        )

        return queryset

    def create(self, request, *args, **kwargs):
        self.organization = get_object_or_404(
            Organization.objects.active(), slug=self.kwargs["org_slug"]
        )

        return super().create(request, *args, **kwargs)

    def perform_destroy(self, instance):
        if self.organization.is_draft:
            # If organization hasn't been published, delete blog post entirely
            return super().perform_destroy(instance)

        # Do a soft delete if the organization has already been published
        instance.is_deleted = True
        instance.save()


class PrivateOrganizationChecklistViewSet(
    mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    """
    Validates all fields of organization and returns the list of invalid or missing data
    """

    schema = AutoSchema(
        tags=["Private", "Organization"],
    )

    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "slug"

    def retrieve(self, request, *args, **kwargs):
        organization = get_object_or_404(
            Organization.objects.active().filter(owner=request.user),
            slug=kwargs[self.lookup_field],
        )

        validation_result = self.validate_organization(organization)

        if bool(validation_result):
            return Response(
                status=status.HTTP_428_PRECONDITION_REQUIRED, data=validation_result
            )

        return Response(status.HTTP_200_OK)

    def validate_organization(self, organization):
        skip_validation = [
            "id",
            "is_verified",
            "is_draft",
            "is_deleted",
            "promote",
            "deadline",
            "updated_at",
            "created_at",
            "owner",
        ]
        validation_errors = {}

        # iterate through all the fields of the model
        for field in organization._meta.get_fields():
            if (
                field.many_to_one
                or field.one_to_many
                or field.one_to_one
                or field.many_to_many
            ):
                related_object = getattr(organization, field.name)

                # Organization must have delivery instructions and products to be published
                if (
                    "instructions" == field.name or "products" == field.name
                ) and not related_object:
                    validation_errors[field.name] = "empty"

            else:
                if field.name in skip_validation:
                    continue

                value = getattr(organization, field.name)

                # For most fields, validate if they are simply not empty
                if not value:
                    validation_errors[field.name] = "empty"
                else:
                    # Check if URL is actually valid, not that it's just there
                    if "url" == field.name:
                        if not self.validate_url(value):
                            validation_errors[field.name] = "invalid"
                    # Check that EIN is, at least, of valid format
                    elif "ein_number" == field.name:
                        if not self.validate_ein(value):
                            validation_errors[field.name] = "invalid"
                    # Check that ZIP is, at least, of valid format
                    elif "zip" == field.name:
                        if not (len(value) == 5 and value.isdigit()):
                            validation_errors[field.name] = "invalid"

        return validation_errors

    def validate_url(self, url):
        response = None
        try:
            response = requests.head(url)
        except:
            return False

        if response.status_code >= 400:
            return False

        return True

    def validate_ein(self, ein_number):
        # Remove any non-digit characters
        ein = re.sub(r"\D", "", ein_number)

        # Check that the length is correct
        if len(ein) != 9:
            return False

        # Check that the first two digits are between 01 and 99
        if not (1 <= int(ein[0:2]) <= 99):
            return False

        # Calculate the check digit
        check_sum = sum([int(ein[i]) * (i % 2 * 2 + 1) for i in range(8)])
        check_digit = (10 - check_sum % 10) % 10

        # Check that the check digit matches the last digit of the EIN
        return check_digit == int(ein[8])
