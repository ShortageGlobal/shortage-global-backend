from rest_framework import serializers

from shortage.apps.blog.models import BlogPost
from shortage.helpers.serializers import AuthorizedUserOrNone


class BlogPostSerializer(serializers.ModelSerializer):
    author = serializers.HiddenField(default=AuthorizedUserOrNone())

    class Meta:
        model = BlogPost
        fields = [
            "owner",
            "author",
            "title",
            "content",
            "is_published",
        ]
