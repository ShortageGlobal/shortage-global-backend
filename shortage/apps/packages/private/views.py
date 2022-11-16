from rest_framework import generics, viewsets, mixins, permissions, filters
from rest_framework.schemas.openapi import AutoSchema
from shortage.apps.catalog.models import Organization
from shortage.apps.packages.models import Package, PackageStatus, PackageType
from shortage.apps.packages.private.package_serializers import PrivatePackageSerializer
from shortage.helpers.permissions import IsObjectOwner


class PrivateOrganizationPackagesViewSet(
    mixins.ListModelMixin, viewsets.GenericViewSet
):
    """List of packages donated to the given organization"""

    schema = AutoSchema(
        tags=["Private", "Packages"],
    )

    permission_classes = [permissions.IsAuthenticated, IsObjectOwner]
    serializer_class = PrivatePackageSerializer

    def get_queryset(self):
        organization = generics.get_object_or_404(
            Organization.objects.public(), slug=self.kwargs["org_slug"]
        )
        return Package.objects.filter(
            items__product__organization=organization
        ).distinct()


class PrivateAccountPackagesViewSet(viewsets.ReadOnlyModelViewSet):
    """List of packages donated by the current user"""

    schema = AutoSchema(
        tags=["Private", "Packages"],
    )

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PrivatePackageSerializer
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ["created_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return (
            Package.objects.filter(owner=self.request.user)
            .exclude(type=PackageType.FUNDED_BY_DONOR, status=PackageStatus.REGISTERED)
            .prefetch_related("items", "items__product", "items__product__organization")
        )
