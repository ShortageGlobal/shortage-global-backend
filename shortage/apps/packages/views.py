from django.shortcuts import get_object_or_404
from rest_framework import viewsets, mixins, permissions
from shortage.apps.catalog.models import Organization, Product
from .models import Package
from .serializers import (
    PackageSerializer,
    PackageCreationSerializer,
)
from shortage.apps.mailing.mail_service import PackageRegistrationEmail


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


class PackageCreationViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    """Create package"""

    permission_classes = [permissions.AllowAny]
    serializer_class = PackageCreationSerializer

    def create(self, request, *args, **kwargs):
        # check organization and store it into view,
        # so serializer could use it for validation
        self.organization = get_object_or_404(
            Organization.objects.public(), slug=self.kwargs["org_slug"]
        )

        package_response = super().create(request, *args, **kwargs)

        uuid = package_response.data["uuid"]
        package = Package.objects.get(uuid=uuid)

        if package.email:
            package_registration_email = PackageRegistrationEmail(
                organization_slug=self.kwargs["org_slug"], package_uuid=package.uuid
            )
            package_registration_email.add_recipient(
                email=package.email, name=package.full_name
            )
            package_registration_email.send()

        return package_response
