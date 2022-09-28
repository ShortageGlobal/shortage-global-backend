from rest_framework import serializers
from shortage.apps.catalog.models import Product
from shortage.apps.catalog.serializers import ProductOrganizationPreviewSerializer


class PrivateProductSerializer(serializers.ModelSerializer):
    photo = serializers.ImageField(source="large_photo", required=False)

    class Meta:
        model = Product
        fields = [
            "name",
            "slug",
            "category",
            "photo",
            "price",
            "requested_amount",
            "description",
            "top_priority",
        ]

    def create(self, validated_data):
        organization = self.context["view"].organization
        validated_data["organization"] = organization

        return Product.objects.create(**validated_data)
