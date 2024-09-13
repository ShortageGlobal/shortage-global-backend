from rest_framework import serializers
from shortage.apps.blog.serializers import BlogPostPreviewSerializer, BlogPostSerializer
from .models import (
    Organization,
    Instruction,
    Product,
    Campaign,
    OrganizationRegistrationRequest,
    DemoRequest,
    OrganizationBlogPost,
)


class OrganizationPreviewSerializer(serializers.ModelSerializer):
    logo = serializers.ImageField(source="medium_logo_photo", read_only=True)

    class Meta:
        model = Organization
        fields = [
            "name",
            "slug",
            "logo",
            "is_draft",
            "is_verified",
        ]


class ExternalOrganizationPreviewSerializer(serializers.ModelSerializer):
    logo = serializers.ImageField(source="medium_logo_photo", read_only=True)

    class Meta:
        model = Organization
        fields = [
            "name",
            "logo",
            "url",
        ]


class InstructionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Instruction
        fields = [
            "name",
            "address_line1",
            "address_line2",
            "city",
            "state_province_region",
            "zip",
            "country",
            "phone_number",
            "comment",
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
        read_only_fields = fields


class ProductPreviewWithOrganizationSerializer(ProductPreviewSerializer):
    organization = OrganizationPreviewSerializer(read_only=True)

    class Meta:
        model = Product
        fields = ProductPreviewSerializer.Meta.fields + [
            "organization",
        ]


class CategorySerializer(serializers.BaseSerializer):
    def to_representation(self, instance):
        return instance


class OrganizationSerializer(serializers.ModelSerializer):
    logo = serializers.ImageField(source="medium_logo_photo", read_only=True)
    banner = serializers.ImageField(source="medium_banner_photo", read_only=True)

    class Meta:
        model = Organization
        fields = [
            "name",
            "slug",
            "requested_goods",
            "mission_description",
            "meta_description",
            "logo",
            "banner",
            "url",
            "deadline",
            "is_draft",
            "is_verified",
        ]


class OrganizationSlugSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = [
            "slug",
        ]


class OrganizationProductSlugSerializer(serializers.ModelSerializer):
    organization = OrganizationSlugSerializer()

    class Meta:
        model = Product
        fields = [
            "slug",
            "organization",
        ]


class OrganizationRegistrationRequestSerializer(serializers.ModelSerializer):
    agreed_to_terms_of_use = serializers.BooleanField(required=True, write_only=True)

    class Meta:
        model = OrganizationRegistrationRequest
        fields = [
            "first_name",
            "last_name",
            "phone_number",
            "email",
            "organization_name",
            "ein_number",
            "url",
            "agreed_to_terms_of_use",
        ]

    def validate_agreed_to_terms_of_use(self, value):
        if not value:
            raise serializers.ValidationError(
                "You must agree to the Terms of Use Policy."
            )
        return value

    def create(self, validated_data):
        # ignore this field after validation
        validated_data.pop("agreed_to_terms_of_use")
        return super().create(validated_data)


class DemoRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = DemoRequest
        fields = [
            "email",
            "source",
        ]


class CampaignPreviewSerializer(serializers.ModelSerializer):
    banner = serializers.ImageField(source="banner_photo_preview", read_only=True)

    class Meta:
        model = Campaign
        fields = [
            "uuid",
            "name",
            "slug",
            "banner",
            "created_at",
            "updated_at",
            "products_count",
            "is_draft",
        ]


class CampaignMinimalPreviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Campaign
        fields = [
            "uuid",
            "name",
            "slug",
            "is_draft",
        ]


class CampaignSerializer(CampaignPreviewSerializer):
    banner = serializers.ImageField(source="banner_photo", read_only=True)

    class Meta:
        model = Campaign
        fields = CampaignPreviewSerializer.Meta.fields + [
            "requested_goods",
            "mission_description",
            "meta_description",
            "deadline",
        ]


class ProductSerializer(serializers.ModelSerializer):
    photo = serializers.ImageField(source="large_photo", read_only=True)
    organization = OrganizationPreviewSerializer(read_only=True)
    campaign = serializers.SerializerMethodField()

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
            "description",
            "top_priority",
            "organization",
            "campaign",
        ]

    def get_campaign(self, obj):
        if hasattr(self.context["view"], "campaign"):
            campaign = self.context["view"].campaign
            serializer = CampaignMinimalPreviewSerializer(instance=campaign)
            return serializer.data
        else:
            return None


class OrganizationBlogPostPreviewSerializer(BlogPostPreviewSerializer):
    organization = OrganizationPreviewSerializer(read_only=True)

    class Meta(BlogPostPreviewSerializer.Meta):
        model = OrganizationBlogPost
        fields = BlogPostPreviewSerializer.Meta.fields + ["organization"]


class OrganizationBlogPostSerializer(BlogPostSerializer):
    organization = OrganizationPreviewSerializer(read_only=True)

    class Meta(BlogPostSerializer.Meta):
        model = OrganizationBlogPost
        fields = BlogPostSerializer.Meta.fields + ["organization"]


class OrganizationBlogPostSlugSerializer(serializers.ModelSerializer):
    organization = OrganizationSlugSerializer()

    class Meta:
        model = OrganizationBlogPost
        fields = ["slug", "organization"]
