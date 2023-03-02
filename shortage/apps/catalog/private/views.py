import requests
from django.conf import settings
from django.core.exceptions import ValidationError
from rest_framework import (
    viewsets,
    mixins,
    filters,
    permissions,
    status,
)
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.schemas.openapi import AutoSchema
from rest_framework import exceptions
from shortage.apps.catalog.models import (
    Product,
    Organization,
    Instruction,
    OrganizationBlogPost,
    validate_ein,
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
from shortage.helpers.organization_checklist import get_organization_checklist


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
        if (
            self.action == "retrieve"
            or self.action == "list"
            or self.action == "checklist"
        ):
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

    @action(detail=True)
    def checklist(self, request, *args, **kwargs):
        organization = self.get_object()
        checklist = get_organization_checklist(organization=organization)
        return Response(status=status.HTTP_200_OK, data=checklist)

    def validate_organization(self, organization):
        fields_to_validate = [
            {"name": "name", "category": "main"},
            {"name": "slug", "category": "main"},
            {"name": "url", "category": "main", "validators": [validate_url]},
            {"name": "logo", "category": "main"},
            {"name": "banner", "category": "main"},
            {"name": "description", "category": "main"},
            {
                "name": "instructions",
                "category": "main",
                "validators": [validate_queryset],
            },
            {"name": "products", "category": "main", "validators": [validate_queryset]},
            {"name": "meta_description", "category": "main"},
            {"name": "ein_number", "category": "tax", "validators": [validate_ein]},
            {"name": "address_line1", "category": "tax"},
            {"name": "address_line2", "category": "tax"},
            {"name": "city", "category": "tax"},
            {"name": "state_province_region", "category": "tax"},
            {"name": "zip", "category": "tax", "validators": [validate_zip]},
            {"name": "country", "category": "tax"},
            {"name": "representative_first_name", "category": "tax"},
            {"name": "representative_last_name", "category": "tax"},
            {"name": "representative_email", "category": "tax"},
            {"name": "representative_phone_number", "category": "tax"},
            {"name": "representative_signature", "category": "tax"},
        ]

        checklist = {}

        # iterate through all the fields of the model
        for field in fields_to_validate:
            value = getattr(organization, field["name"])
            severity = "WARNING" if field["category"] == "tax" else "ERROR"

            if not checklist.get(field["category"]):
                checklist[field["category"]] = []

            if not value:
                checklist[field["category"]].append(
                    {
                        "field": field["name"],
                        "message": "Value does not exist or is empty",
                        "severity": severity,
                    }
                )
            elif field.get("validators"):
                for validator in field["validators"]:
                    try:
                        validator(value)
                    except ValidationError as exception:
                        checklist[field["category"]].append(
                            {
                                "field": field["name"],
                                "message": exception.message,
                                "severity": severity,
                            }
                        )

        return checklist


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


def validate_url(url):
    response = None
    try:
        response = requests.head(url)
    except Exception as exc:
        raise ValidationError("This is not a valid URL or this URL does not exist")

    if response.status_code >= 400:
        raise ValidationError("This is not a valid URL or this URL does not exist")


def validate_queryset(queryset):
    if 0 == queryset.count():
        raise ValidationError("Query set is empty")


def validate_zip(zip):
    if not (len(zip) == 5 and zip.isdigit()):
        raise ValidationError("Zip code is not a valid US zip code")
