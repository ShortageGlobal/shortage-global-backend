from rest_framework import generics, viewsets, mixins, permissions, filters, status
from rest_framework.schemas.openapi import AutoSchema
from rest_framework.response import Response
from rest_framework.decorators import action
from shortage.apps.catalog.models import Organization, OrganizationBlogPost
from shortage.apps.catalog.serializers import OrganizationBlogPostPreviewSerializer
from shortage.apps.packages.models import Package, PackageStatus, PackageType
from shortage.apps.packages.private.package_serializers import (
    PrivateOrganizationPackageSerializer,
    PrivateOrganizationPackageTaxDeductionReceiptSerializer,
    PrivateAccountPackageSerializer,
)
from shortage.helpers.permissions import IsObjectOwner


class PrivateOrganizationPackagesViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    """List of packages donated to the given organization"""

    schema = AutoSchema(
        tags=["Private", "Packages"],
    )

    permission_classes = [permissions.IsAuthenticated, IsObjectOwner]
    filter_backends = [filters.OrderingFilter]
    ordering = ["-created_at"]
    serializer_class = PrivateOrganizationPackageSerializer

    def get_serializer(self, *args, **kwargs):
        return super().get_serializer(*args, **kwargs)

    def get_queryset(self):
        organization = generics.get_object_or_404(
            Organization.objects.active(), slug=self.kwargs["org_slug"]
        )
        return (
            Package.objects.filter(organization=organization)
            .exclude(type=PackageType.FUNDED_BY_DONOR, status=PackageStatus.REGISTERED)
            .prefetch_related(
                "items",
                "items__product",
                "blog_posts",
            )
        )

    @action(detail=True, methods=["POST"])
    def upload_tax_deduction_receipt(self, request, *args, **kwargs):
        """Upload tax receipt file"""
        package = self.get_object()
        serializer = PrivateOrganizationPackageTaxDeductionReceiptSerializer(
            package, data=request.data
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # return package after saving
        serializer = PrivateOrganizationPackageTaxDeductionReceiptSerializer(
            package, context=self.get_serializer_context()
        )
        return Response(serializer.data)

    @action(detail=True, methods=["POST"])
    def generate_tax_deduction_receipt(self, request, *args, **kwargs):
        """Generate tax receipt file"""
        package = self.get_object()

        if not package.can_generate_tax_receipt():
            return Response(
                status=status.HTTP_428_PRECONDITION_REQUIRED,
                data={"details": "Tax Information is required."},
            )

        package.generate_tax_receipt(force=True, save=True)
        serializer = PrivateOrganizationPackageTaxDeductionReceiptSerializer(
            package, context=self.get_serializer_context()
        )
        return Response(serializer.data)


class PrivateAccountPackagesViewSet(viewsets.ReadOnlyModelViewSet):
    """List of packages donated by the current user"""

    schema = AutoSchema(
        tags=["Private", "Packages"],
    )

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PrivateAccountPackageSerializer
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ["created_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return (
            Package.objects.filter(owner=self.request.user)
            .exclude(type=PackageType.FUNDED_BY_DONOR, status=PackageStatus.REGISTERED)
            .prefetch_related(
                "organization",
                "items",
                "items__product",
            )
        )


class PrivatePackageBlogPostsViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """List of impact stories associated with the packages of the given user"""

    schema = AutoSchema(
        tags=["Private", "Packages"],
    )

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = OrganizationBlogPostPreviewSerializer
    paginator = None

    def get_queryset(self):
        return (
            OrganizationBlogPost.objects.public()
            .filter(
                packageblogpost__package__in=Package.objects.filter(
                    owner=self.request.user
                )
            )
            .distinct()
            .prefetch_related("organization")
            .order_by("-updated_at")
        )
