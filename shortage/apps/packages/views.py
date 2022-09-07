from django.shortcuts import get_object_or_404
from rest_framework import viewsets, mixins, permissions
from shortage.apps.catalog.models import Organization
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Package
from .serializers import (
    PackageSerializer,
    PackageCreationSerializer,
)
from shortage.apps.mailing.mail_service import PackageRegistrationEmail


class PackageViewSet(
    LoginRequiredMixin,
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = [permissions.IsAuthenticated]

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

        return (
            Package.objects.all()
            .filter(package_items__product__organization=organization, owner=owner)
            .distinct()
        )

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
