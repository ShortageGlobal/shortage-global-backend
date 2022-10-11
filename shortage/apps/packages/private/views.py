from rest_framework import generics, viewsets, mixins, permissions
from rest_framework.schemas.openapi import AutoSchema

from shortage.apps.catalog.models import Organization
from shortage.apps.packages.models import Package
from shortage.apps.packages.private.package_serializers import PrivatePackageSerializer
from shortage.helpers.permissions import IsObjectOwner


class PrivateOrganizationPackagesViewSet(
    mixins.ListModelMixin, viewsets.GenericViewSet
):

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
            items__product__organization=organization, owner=self.request.user
        ).distinct()
