from rest_framework import viewsets, permissions
from rest_framework.schemas.openapi import AutoSchema

from shortage.apps.blog.serializers import BlogPostSerializer
from shortage.helpers.permissions import IsObjectOwner


class BlogPostViewSet(viewsets.ModelViewSet):
    schema = AutoSchema(
        tags=["Blog"],
    )

    permission_classes = [permissions.IsAuthenticated, IsObjectOwner]
    serializer_class = BlogPostSerializer
