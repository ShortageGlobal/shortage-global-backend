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
            "need_tax_deduction",
            "first_name",
            "last_name",
            "phone_number",
            "email",
            "address_line1",
            "address_line2",
            "city",
            "state_province_region",
            "zip",
            "country",
            "delivery_company",
            "tracking_code",
            "note",
            "status",
            "photo",
            "type",
            "items",
            "tax_deduction_receipt",
            "created_at",
        ]
        read_only_fields = fields
