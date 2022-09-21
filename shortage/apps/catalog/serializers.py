from rest_framework import serializers
from .models import Organization, Instruction, Product, OnlineStore
from shortage.helpers.serializers import AuthorizedUserOrNone


class OrganizationPreviewSerializer(serializers.ModelSerializer):
    photo = serializers.ImageField(source="medium_photo", read_only=True)

    class Meta:
        model = Organization
        fields = [
            "name",
            "slug",
            "photo",
        ]


class PrivateOrganizationSerializer(serializers.ModelSerializer):
    photo = serializers.ImageField(required=False)
    owner = serializers.HiddenField(default=AuthorizedUserOrNone())

    class Meta:
        model = Organization
        fields = [
            "owner",
            "name",
            "slug",
            "description",
            "photo",
            "url",
            "ein_number",
            "is_verified",
            "is_draft",
        ]
        read_only_fields = ["is_verified"]


class InstructionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Instruction
        fields = [
            "name",
            "description",
            "country",
        ]


class ProductPreviewSerializer(serializers.ModelSerializer):
    photo = serializers.ImageField(source="medium_photo", read_only=True)

    class Meta:
        model = Product
        fields = [
            "name",
            "slug",
            "category",
            "photo",
            "price",
            "requested_amount",
            "top_priority",
            "position",
        ]


class ProductOrganizationPreviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = [
            "name",
            "slug",
        ]


class PromotedProductPreviewSerializer(ProductPreviewSerializer):
    organization = ProductOrganizationPreviewSerializer(read_only=True)

    class Meta:
        model = Product
        fields = ProductPreviewSerializer.Meta.fields + [
            "organization",
        ]


class CategorySerializer(serializers.BaseSerializer):
    def to_representation(self, instance):
        return instance


class OrganizationSerializer(serializers.ModelSerializer):
    photo = serializers.ImageField(source="medium_photo", read_only=True)

    class Meta:
        model = Organization
        fields = [
            "name",
            "slug",
            "description",
            "photo",
            "url",
        ]


class ProductSerializer(serializers.ModelSerializer):
    photo = serializers.ImageField(source="large_photo", read_only=True)
    organization = ProductOrganizationPreviewSerializer(read_only=True)

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
            "organization",
        ]


class OnlineStoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = OnlineStore
        fields = ["url", "name"]
