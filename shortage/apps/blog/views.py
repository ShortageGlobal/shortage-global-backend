import logging

from rest_framework import viewsets, permissions
from rest_framework.schemas.openapi import AutoSchema
from bs4 import BeautifulSoup
from shortage.apps.blog.models import BlogPost
from shortage.apps.blog.serializers import PrivateBlogPostSerializer
from shortage.apps.storage import MediaStorage


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
        # Delete all related images
        storage = MediaStorage()
        soup = BeautifulSoup(instance.content, features="html.parser")
        for img in soup.findAll("img"):
            file_path = img.get("src")

            logging.error(file_path)
            if storage.exists(file_path):
                logging.error("Exists")
                storage.delete(file_path)

        super().perform_destroy(instance)
