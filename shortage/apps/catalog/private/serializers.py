from rest_framework import serializers
from shortage.apps.catalog.models import Organization, Product
from shortage.helpers.serializers import AuthorizedUserOrNone


class PrivateOrganizationWriteSerializer(serializers.ModelSerializer):
    owner = serializers.HiddenField(default=AuthorizedUserOrNone())
    logo = serializers.ImageField(required=False)
    banner = serializers.ImageField(required=False)

    class Meta:
        model = Organization
        fields = [
            "owner",
            "name",
            "slug",
            "description",
            "meta_description",
            "logo",
            "banner",
            "url",
            "ein_number",
            "is_verified",
            "is_draft",
            "promote",
            "deadline",
        ]


class PrivateOrganizationReadSerializer(PrivateOrganizationWriteSerializer):
    logo = serializers.ImageField(required=False, source="medium_logo_photo")
    banner = serializers.ImageField(required=False, source="medium_banner_photo")

    class Meta(PrivateOrganizationWriteSerializer.Meta):
        fields = PrivateOrganizationWriteSerializer.Meta.fields + [
            "updated_at",
            "created_at",
        ]
        read_only_fields = fields


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
