from rest_framework import serializers
from shortage.apps.catalog.models import Product
from shortage.apps.catalog.serializers import OrganizationPreviewSerializer
from shortage.apps.packages.models import Package, PackageItem


class PrivateOrganizationPackageItemProductSerializer(serializers.ModelSerializer):
    photo = serializers.ImageField(source="medium_photo", read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "slug",
            "category",
            "photo",
            "price",
            "requested_amount",
            "is_deleted",
            "top_priority",
        ]


class PrivateOrganizationPackageItemSerializer(serializers.ModelSerializer):
    product = PrivateOrganizationPackageItemProductSerializer()

    class Meta:
        model = PackageItem
        fields = ["quantity", "product"]


class PrivateOrganizationPackageSerializer(serializers.ModelSerializer):
    items = PrivateOrganizationPackageItemSerializer(many=True)

    class Meta:
        model = Package
        fields = [
            "uuid",
            "items",
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
            "tax_deduction_receipt",
            "blog_posts",
            "created_at",
        ]


class PrivateOrganizationPackageTaxDeductionReceiptSerializer(
    serializers.ModelSerializer
):
    class Meta:
        model = Package
        fields = ["tax_deduction_receipt"]


class PrivateAccountPackageItemProductSerializer(serializers.ModelSerializer):
    photo = serializers.ImageField(source="medium_photo", read_only=True)

    class Meta:
        model = Product
        fields = [
            "name",
            "slug",
            "category",
            "photo",
            "price",
        ]


class PrivateAccountPackageItemSerializer(PrivateOrganizationPackageItemSerializer):
    product = PrivateAccountPackageItemProductSerializer()


class PrivateAccountPackageSerializer(PrivateOrganizationPackageSerializer):
    organization = OrganizationPreviewSerializer(read_only=True)
    items = PrivateAccountPackageItemSerializer(many=True)

    class Meta(PrivateOrganizationPackageSerializer.Meta):
        fields = PrivateOrganizationPackageSerializer.Meta.fields + ["organization"]
        read_only_fields = fields
