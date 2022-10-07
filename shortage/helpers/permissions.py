from rest_framework.generics import get_object_or_404
from rest_framework.permissions import BasePermission

from shortage.apps.catalog.models import Organization


class IsObjectOwner(BasePermission):
    def __init__(self):
        self.organization = None

    def has_permission(self, request, view):
        if not self.organization:
            self.organization = get_object_or_404(
                Organization.objects.public(), slug=view.kwargs["org_slug"]
            )

        return request.user == self.organization.owner

    def has_object_permission(self, request, view, obj):
        if not self.organization:
            self.organization = get_object_or_404(
                Organization.objects.public(), slug=view.kwargs["org_slug"]
            )

        # Todo: Figure out a way to check ownership of the object itself
        return request.user == self.organization.owner
