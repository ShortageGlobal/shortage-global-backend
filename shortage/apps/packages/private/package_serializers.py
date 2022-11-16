from rest_framework import serializers
from shortage.apps.catalog.models import Product, Organization
from shortage.apps.packages.models import Package, PackageItem


class PrivatePackageItemProductOrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = [
            "name",
            "slug",
        ]


class PrivatePackageItemProductSerializer(serializers.ModelSerializer):
    photo = serializers.ImageField(source="medium_photo", read_only=True)
    organization = PrivatePackageItemProductOrganizationSerializer()

    class Meta:
        model = Product
        fields = [
            "name",
            "slug",
            "category",
            "photo",
            "price",
            "requested_amount",
            "organization",
        ]


class PrivatePackageItemSerializer(serializers.ModelSerializer):
    product = PrivatePackageItemProductSerializer()

    class Meta:
        model = PackageItem
        fields = ["quantity", "product"]


class PrivatePackageSerializer(serializers.ModelSerializer):
    items = PrivatePackageItemSerializer(many=True)

    class Meta:
        model = Package
        fields = [
            "uuid",
            "first_name",
            "last_name",
            "email",
            "phone_number",
            "delivery_company",
            "tracking_code",
            "note",
            "status",
            "photo",
            "type",
            "items",
            "created_at",
        ]
        read_only_fields = fields
