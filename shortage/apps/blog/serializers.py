from rest_framework import serializers
from rest_framework.fields import CurrentUserDefault
from shortage.apps.blog.models import BlogPost
from .models import ShortageBlogPost


class PrivateBlogPostSerializer(serializers.ModelSerializer):
    author = serializers.HiddenField(default=CurrentUserDefault())

    class Meta:
        # this will fail as BlogPost is abstract. Inherit from this class.
        model = BlogPost
        fields = [
            "uuid",
            "author",
            "title",
            "content",
            "is_draft",
        ]


class BlogPostPreviewSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(source="card_preview")

    class Meta:
        # this will fail as BlogPost is abstract. Inherit from this class.
        model = BlogPost
        fields = [
            "uuid",
            "title",
            "slug",
            "image",
            "created_at",
            "updated_at",
            "is_draft",
        ]
        read_only_fields = fields


class BlogPostSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(source="large_image")

    class Meta:
        # this will fail as BlogPost is abstract. Inherit from this class.
        model = BlogPost
        fields = [
            "uuid",
            "title",
            "slug",
            "image",
            "content",
            "meta_description",
            "created_at",
            "updated_at",
            "is_draft",
        ]
        read_only_fields = fields


class ShortageBlogPostPreviewSerializer(BlogPostPreviewSerializer):
    class Meta(BlogPostPreviewSerializer.Meta):
        model = ShortageBlogPost


class ShortageBlogPostSerializer(BlogPostSerializer):
    class Meta(BlogPostSerializer.Meta):
        model = ShortageBlogPost


class ShortageBlogPostSlugSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShortageBlogPost
        fields = ["slug"]
