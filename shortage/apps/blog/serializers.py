from rest_framework import serializers
from rest_framework.fields import CurrentUserDefault

from shortage.apps.blog.models import BlogPost
from shortage.apps.catalog.serializers import ProductOrganizationPreviewSerializer


class PrivateBlogPostSerializer(serializers.ModelSerializer):
    author = serializers.HiddenField(default=CurrentUserDefault())
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

    def validate(self, attrs):
        # Check that organization matches the author and package items
        organization = self.context["view"].organization
        author = attrs["author"]

        if organization.owner != author:
            raise serializers.ValidationError("Author and org owner don't match")

        for package in attrs["packages"]:
            if package.owner and package.owner != organization.owner:
                raise serializers.ValidationError("Package and org owner don't match")

        return super().validate(attrs)

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
