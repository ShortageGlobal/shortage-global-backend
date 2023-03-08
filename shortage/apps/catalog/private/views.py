from django.conf import settings
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
from shortage.apps.mailing.mail_service import (
    OrganizationVerificationRequestServiceEmail,
)
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
    mixins.DestroyModelMixin,
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
        if self.action in [
            "list",
            "retrieve",
            "checklist",
            "publish",
            "unpublish",
            "destroy",
        ]:
            return (
                Organization.objects.active()
                .filter(owner=self.request.user)
                .order_by("-created_at")
            )
        else:
            # Prevent changes to organizations which you don't own and which are published
            return Organization.objects.editable().filter(owner=self.request.user)

    def create(self, request, *args, **kwargs):
        # Allow only one organization per user
        if Organization.objects.active().filter(owner=self.request.user).exists():
            raise OneOrganizationPerUser()

        return super().create(request, *args, **kwargs)

    def perform_destroy(self, instance):
        # Do a soft delete
        instance.is_deleted = True
        instance.save()

    @action(detail=True)
    def checklist(self, request, *args, **kwargs):
        organization = self.get_object()
        checklist = get_organization_checklist(organization=organization)
        return Response(status=status.HTTP_200_OK, data=checklist)

    @action(detail=True, methods=["POST"])
    def publish(self, request, *args, **kwargs):
        """Publish organization for verification"""
        organization = self.get_object()
        checklist = get_organization_checklist(organization=organization)

        if not checklist["can_publish"]:
            return Response(
                status=status.HTTP_428_PRECONDITION_REQUIRED,
                data={
                    "details": "Organization doesn't satisfy publishing requirements."
                },
            )

        organization.is_draft = False
        organization.is_verified = False
        organization.save()

        # notify staff
        OrganizationVerificationRequestServiceEmail(organization).send()

        serializer = PrivateOrganizationReadSerializer(
            organization, context=self.get_serializer_context()
        )
        return Response(serializer.data)

    @action(detail=True, methods=["POST"])
    def unpublish(self, request, *args, **kwargs):
        """Make the organization draft again"""
        organization = self.get_object()
        organization.is_draft = True
        organization.is_verified = False
        organization.save()

        serializer = PrivateOrganizationReadSerializer(
            organization, context=self.get_serializer_context()
        )
        return Response(serializer.data)


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
        # TODO: prevent editing/deleting if organization is not in draft state
        # (except for "requrested_amount" and "position")
        queryset = Product.objects.active().filter(organization=self.organization)

        # filter by category
        category = self.request.query_params.get("category")
        if category:
            queryset = queryset.filter(category=category)

        return queryset

    def create(self, request, *args, **kwargs):
        self.organization = get_object_or_404(
            Organization.objects.editable(), slug=self.kwargs["org_slug"]
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
        org_queryset = (
            Organization.objects.active()
            if self.action in ["list", "retrieve"]
            else Organization.objects.editable()
        )
        organization = get_object_or_404(org_queryset, slug=self.kwargs["org_slug"])
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
        # Do a soft delete
        instance.is_deleted = True
        instance.save()
