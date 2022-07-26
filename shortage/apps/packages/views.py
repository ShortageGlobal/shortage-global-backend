from rest_framework import viewsets, mixins
from django.shortcuts import get_object_or_404
from shortage.apps.catalog.models import Organization
from .models import Package
from .serializers import PackageSerializer


class PackageViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """Package details for the given uuid and the given organization"""

    serializer_class = PackageSerializer

    def get_queryset(self):
        organization = get_object_or_404(
            Organization.objects.public(), slug=self.kwargs["org_slug"]
        )
        return Package.objects.filter(
            package_items__product__organization=organization
        ).distinct()
