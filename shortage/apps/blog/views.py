import logging

from rest_framework import viewsets, permissions, mixins
from rest_framework.schemas.openapi import AutoSchema
from rest_framework.generics import get_object_or_404
from bs4 import BeautifulSoup
from shortage.apps.blog.models import BlogPost
from shortage.apps.blog.serializers import PrivateBlogPostSerializer, BlogPostSerializer
from shortage.apps.catalog.models import Organization
from shortage.apps.packages.models import Package
from shortage.apps.storage import MediaStorage
from shortage.helpers.permissions import IsObjectOwner
import os


class PrivateBlogPostViewSet(viewsets.ModelViewSet):
    schema = AutoSchema(
        tags=["Private", "Blog"],
    )

    permission_classes = [permissions.IsAuthenticated, IsObjectOwner]
    serializer_class = PrivateBlogPostSerializer

    def get_queryset(self):
        self.organization = get_object_or_404(
            Organization.objects.public(), slug=self.kwargs["org_slug"]
        )

        queryset = BlogPost.objects.filter(organization=self.organization)

        is_published = self.request.query_params.get("is_published")
        if is_published:
            queryset = queryset.filter(is_published=is_published)

        return queryset

    def create(self, request, *args, **kwargs):
        self.organization = get_object_or_404(
            Organization.objects.public(), slug=self.kwargs["org_slug"]
        )

        return super().create(request, *args, **kwargs)

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


class RelatedBlogPostsViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    schema = AutoSchema(
        tags=["Packages", "Blog"],
    )

    permission_classes = [permissions.AllowAny]
    serializer_class = BlogPostSerializer

    def get_queryset(self):
        organization = get_object_or_404(
            Organization.objects.public(), slug=self.kwargs["org_slug"]
        )
        package = get_object_or_404(Package.objects.all(), uuid=self.kwargs["pk"])

        queryset = BlogPost.objects.all().filter(
            organization=organization, packages__in=[str(package.uuid)]
        )

        return queryset
