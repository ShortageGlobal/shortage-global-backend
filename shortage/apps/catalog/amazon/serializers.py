from rest_framework import serializers

from shortage.apps.catalog.amazon.models import AmazonProduct


class AmazonProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = AmazonProduct
        fields = [
            "asin",
            "title",
            "description",
            "price",
            "link",
            "image_url",
        ]
