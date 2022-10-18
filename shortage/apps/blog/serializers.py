from rest_framework import serializers

from shortage.apps.blog.models import BlogPost
from shortage.apps.catalog.serializers import ProductOrganizationPreviewSerializer
from shortage.helpers.serializers import AuthorizedUserOrNone


class PrivateBlogPostSerializer(serializers.ModelSerializer):
    author = serializers.HiddenField(default=AuthorizedUserOrNone())
    organization = ProductOrganizationPreviewSerializer(read_only=True)

    class Meta:
        model = BlogPost
        fields = [
            "uuid",
            "organization",
            "author",
            "title",
            "content",
            "packages",
            "is_published",
        ]

    def create(self, validated_data):
        organization = self.context["view"].organization
        validated_data["organization"] = organization

        return super().create(validated_data)

class BlogPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlogPost
        fields = [
            "uuid",
            "organization",
            "author",
            "title",
            "content",
            "packages",
            "is_published",
        ]
        read_only_fields = fields
