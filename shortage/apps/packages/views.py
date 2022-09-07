from django.shortcuts import get_object_or_404
from rest_framework import viewsets, mixins, permissions, response
from shortage.apps.catalog.models import Organization
from .models import Package
from .serializers import (
    PackageSerializer,
    PackageCreationSerializer,
)

from shortage.apps.mailing.mail_service import PackageRegistrationEmail


class PackageViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = [permissions.AllowAny]

    def get_serializer_class(self):
        if "GET" == self.request.method:
            return PackageSerializer

        return PackageCreationSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()

        context["organization"] = get_object_or_404(
            Organization.objects.public(), slug=self.kwargs["org_slug"]
        )
        context["user"] = self.request.user

        return context

    def get_queryset(self):
        organization = self.get_serializer_context()["organization"]
        owner = self.get_serializer_context()["user"]

        queryset = Package.objects.all().filter(package_items__product__organization=organization).distinct()

        # Return everything for the org's owner
        if owner.is_authenticated and owner == organization.owner:
            pass
        # Return only user's items if he is not an org owner
        elif owner.is_authenticated and owner != organization.owner:
            queryset = queryset.filter(owner=owner)
        # For everyone else - return nothing
        else:
            queryset = Package.objects.none()

        return queryset

    def create(self, request, *args, **kwargs):
        package_response = super().create(request, *args, **kwargs)

        uuid = package_response.data["uuid"]
        package = Package.objects.get(uuid=uuid)

        # if package.email:
        #     package_registration_email = PackageRegistrationEmail(
        #         organization_slug=self.kwargs["org_slug"], package_uuid=package.uuid
        #     )
        #     package_registration_email.add_recipient(
        #         email=package.email, name=package.full_name
        #     )
        #     package_registration_email.send()

        return package_response
