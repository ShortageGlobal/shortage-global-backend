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
            "organization",
            "author",
            "title",
            "content",
            "is_published",
        ]

    def create(self, validated_data):
        organization = self.context["view"].organization
        validated_data["organization"] = organization

        return BlogPost.objects.create(**validated_data)
