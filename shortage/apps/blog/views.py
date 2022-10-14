from rest_framework import viewsets, permissions
from rest_framework.schemas.openapi import AutoSchema
from rest_framework.generics import get_object_or_404

from shortage.apps.blog.models import BlogPost
from shortage.apps.blog.serializers import PrivateBlogPostSerializer
from shortage.apps.catalog.models import Organization
from shortage.helpers.permissions import IsObjectOwner


class PrivateBlogPostViewSet(viewsets.ModelViewSet):
    schema = AutoSchema(
        tags=["Private", "Blog"],
    )

    permission_classes = [permissions.IsAuthenticated, IsObjectOwner]
    serializer_class = PrivateBlogPostSerializer

    def __init__(self):
        self.organization = None

    def get_queryset(self):
        organization = get_object_or_404(
            Organization.objects.public(), slug=self.kwargs["org_slug"]
        )

        return BlogPost.objects.filter(organization=organization)

    def create(self, request, *args, **kwargs):
        self.organization = get_object_or_404(
            Organization.objects.public(), slug=self.kwargs["org_slug"]
        )

        return super().create(request, *args, **kwargs)
