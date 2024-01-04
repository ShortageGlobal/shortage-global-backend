from rest_framework import serializers
from shortage.apps.catalog.models import Campaign, Product, OrganizationBlogPost
from shortage.apps.catalog.serializers import (
    OrganizationPreviewSerializer,
    CampaignMinimalPreviewSerializer,
)
from shortage.apps.packages.models import Package, PackageItem


class PrivateOrganizationPackageItemProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = [
            "id",
            "slug",
            "is_deleted",
        ]


class PrivateOrganizationPackageItemSerializer(serializers.ModelSerializer):
    product = PrivateOrganizationPackageItemProductSerializer()
    photo = serializers.ImageField(source="medium_photo", read_only=True)

    class Meta:
        model = PackageItem
        fields = ["quantity", "price", "name", "photo", "category", "product"]


class PrivateOrganizationPackageCampaignSerializer(CampaignMinimalPreviewSerializer):
    class Meta:
        model = Campaign
        fields = CampaignMinimalPreviewSerializer.Meta.fields + [
            "is_deleted",
        ]


class PrivateOrganizationPackageSerializer(serializers.ModelSerializer):
    items = PrivateOrganizationPackageItemSerializer(many=True)
    campaign = PrivateOrganizationPackageCampaignSerializer(read_only=True)

    class Meta:
        model = Package
        fields = [
            "uuid",
            "items",
            "campaign",
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


class PrivateOrganizationPackageBlogPostsSerializer(serializers.ModelSerializer):
    blog_posts = serializers.PrimaryKeyRelatedField(
        many=True, queryset=OrganizationBlogPost.objects.all()
    )

    class Meta:
        model = Package
        fields = [
            "blog_posts",
        ]

    def validate(self, attrs):
        # TODO: validate blog posts belong to the same organization
        return super().validate(attrs)


class PrivateOrganizationPackageTaxDeductionReceiptSerializer(
    serializers.ModelSerializer
):
    class Meta:
        model = Package
        fields = ["tax_deduction_receipt"]


class PrivateAccountPackageSerializer(PrivateOrganizationPackageSerializer):
    organization = OrganizationPreviewSerializer(read_only=True)
    items = PrivateOrganizationPackageItemSerializer(many=True)

    class Meta(PrivateOrganizationPackageSerializer.Meta):
        fields = PrivateOrganizationPackageSerializer.Meta.fields + ["organization"]
        read_only_fields = fields
