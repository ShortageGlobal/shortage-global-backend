import logging

from rest_framework import viewsets, permissions
from rest_framework.schemas.openapi import AutoSchema
from shortage.apps.blog.models import BlogPost
from shortage.apps.blog.serializers import PrivateBlogPostSerializer


class BlogPostViewSet(viewsets.ModelViewSet):
    schema = AutoSchema(
        tags=["Private", "Blog"],
    )

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PrivateBlogPostSerializer

    def get_queryset(self):
        queryset = BlogPost.objects.all()

        is_published = self.request.query_params.get("is_published")

        if is_published:
            is_published = is_published.lower()

            if is_published != "true" and is_published != "false":
                raise ValueError("is_published should be either true or false")

            queryset = queryset.filter(is_published=is_published)

        return queryset

    def perform_destroy(self, instance):
        # Todo: Delete all related images

        super().perform_destroy(instance)
