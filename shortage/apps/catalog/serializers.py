from rest_framework import serializers
from .models import (
    Organization,
    Instruction,
    Product,
    OrganizationRegistrationRequest,
)
from shortage.helpers.serializers import AuthorizedUserOrNone


class OrganizationPreviewSerializer(serializers.ModelSerializer):
    logo = serializers.ImageField(source="medium_logo_photo", read_only=True)

    class Meta:
        model = Organization
        fields = [
            "name",
            "slug",
            "logo",
        ]


class PrivateOrganizationSerializer(serializers.ModelSerializer):
    logo = serializers.ImageField(required=False)
    banner = serializers.ImageField(required=False)
    owner = serializers.HiddenField(default=AuthorizedUserOrNone())

    class Meta:
        model = Organization
        fields = [
            "owner",
            "name",
            "slug",
            "description",
            "logo",
            "banner",
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
        read_only_fields = fields


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
    logo = serializers.ImageField(source="medium_logo_photo", read_only=True)
    banner = serializers.ImageField(source="medium_banner_photo", read_only=True)

    class Meta:
        model = Organization
        fields = [
            "name",
            "slug",
            "description",
            "logo",
            "banner",
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
