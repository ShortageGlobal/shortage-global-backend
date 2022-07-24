from calendar import c
from rest_framework import serializers
from .models import Organization, Instruction, Product, OnlineStore


class OrganizationPreviewSerializer(serializers.ModelSerializer):
    photo = serializers.ImageField(source="medium_photo", read_only=True)

    class Meta:
        model = Organization
        fields = [
            "name",
            "slug",
            "photo",
        ]


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


class PromotedProductPreviewSerializer(ProductPreviewSerializer):
    organization_name = serializers.CharField(source="organization.name")
    organization_slug = serializers.CharField(source="organization.slug")

    class Meta:
        model = Product
        fields = ProductPreviewSerializer.Meta.fields + [
            "organization_name",
            "organization_slug",
        ]


class CategorySerializer(serializers.BaseSerializer):
    def to_representation(self, instance):
        return instance


class PublicOrganizationSerializer(serializers.ModelSerializer):
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


class OnlineStoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = OnlineStore
        fields = ["url", "name"]
