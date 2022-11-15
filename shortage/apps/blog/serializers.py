from rest_framework import serializers
from rest_framework.fields import CurrentUserDefault

from shortage.apps.blog.models import BlogPost
from shortage.apps.catalog.serializers import ProductOrganizationPreviewSerializer


class PrivateBlogPostSerializer(serializers.ModelSerializer):
    author = serializers.HiddenField(default=CurrentUserDefault())

    class Meta:
        model = BlogPost
        fields = [
            "uuid",
            "author",
            "title",
            "content",
            "is_published",
        ]


class BlogPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlogPost
        fields = [
            "uuid",
            "author",
            "title",
            "content",
            "is_published",
        ]
        read_only_fields = fields
