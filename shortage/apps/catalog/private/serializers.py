from rest_framework import serializers
from rest_framework.fields import CurrentUserDefault
from shortage.apps.catalog.models import (
    Organization,
    Product,
    Instruction,
    OrganizationBlogPost,
)


class PrivateOrganizationWriteSerializer(serializers.ModelSerializer):
    owner = serializers.HiddenField(default=CurrentUserDefault())

    class Meta:
        model = Organization
        fields = [
            "owner",
            "name",
            "slug",
            "description",
            "requested_goods",
            "mission_description",
            "meta_description",
            "logo",
            "banner",
            "url",
            "ein_number",
            "is_verified",
            "is_draft",
            "promote",
            "deadline",
            "address_line1",
            "address_line2",
            "city",
            "state_province_region",
            "zip",
            "country",
            "representative_first_name",
            "representative_last_name",
            "representative_email",
            "representative_phone_number",
            "representative_signature",
            "tax_deduction_receipt_preamble",
            "tax_deduction_receipt_legal_information",
        ]
        read_only_fields = [
            "is_verified",
            "is_draft",  # there is a special route for publishing an organization
            "promote",
        ]


class PrivateOrganizationReadSerializer(PrivateOrganizationWriteSerializer):
    logo = serializers.ImageField(source="medium_logo_photo")
    banner = serializers.ImageField(source="medium_banner_photo")

    class Meta(PrivateOrganizationWriteSerializer.Meta):
        fields = PrivateOrganizationWriteSerializer.Meta.fields + [
            "updated_at",
            "created_at",
        ]
        read_only_fields = fields


class PrivateProductWriteSerializer(serializers.ModelSerializer):
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
            "position",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def validate_slug(self, value):
        """
        Validate UniqueConstraint constraint.
        DRF currently doesn't create validators for them automatically.
        See: https://github.com/encode/django-rest-framework/issues/7173
        """
        another_product = Product.objects.filter(slug=value)
        if self.instance:
            # if we edit product, exclude current instance from queryset
            another_product = another_product.exclude(id=self.instance.id)
        if another_product.exists():
            raise serializers.ValidationError("This address has already been taken.")
        return value

    def create(self, validated_data):
        organization = self.context["view"].organization
        validated_data["organization"] = organization

        return Product.objects.create(**validated_data)


class PrivateProductReadSerializer(PrivateProductWriteSerializer):
    photo = serializers.ImageField(source="medium_photo", required=False)

    class Meta(PrivateProductWriteSerializer.Meta):
        fields = PrivateProductWriteSerializer.Meta.fields
        read_only_fields = fields


class PrivateInstructionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Instruction
        fields = [
            "id",
            "name",
            "description",
            "address_line1",
            "address_line2",
            "city",
            "state_province_region",
            "zip",
            "country",
            "phone_number",
            "comment",
        ]

    def create(self, validated_data):
        organization = self.context["view"].organization
        validated_data["organization"] = organization

        return Instruction.objects.create(**validated_data)


class PrivateOrganizationBlogPostWriteSerializer(serializers.ModelSerializer):
    author = serializers.HiddenField(default=CurrentUserDefault())

    class Meta:
        model = OrganizationBlogPost
        fields = [
            "author",
            "uuid",
            "title",
            "slug",
            "content",
            "meta_description",
            "image",
            "is_draft",
            "promote",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["uuid", "promote", "created_at", "updated_at"]

    def validate_slug(self, value):
        """
        Validate UniqueConstraint constraint.
        DRF currently doesn't create validators for them automatically.
        See: https://github.com/encode/django-rest-framework/issues/7173
        """
        another_blog_post = OrganizationBlogPost.objects.filter(slug=value)
        if self.instance:
            # if we edit blog post, exclude current instance from queryset
            another_blog_post = another_blog_post.exclude(uuid=self.instance.uuid)
        if another_blog_post.exists():
            raise serializers.ValidationError("This address has already been taken.")
        return value

    def create(self, validated_data):
        organization = self.context["view"].organization
        validated_data["organization"] = organization

        return OrganizationBlogPost.objects.create(**validated_data)


class PrivateOrganizationBlogPostReadSerializer(
    PrivateOrganizationBlogPostWriteSerializer
):
    image = serializers.ImageField(source="card_preview", required=False)

    class Meta(PrivateOrganizationBlogPostWriteSerializer.Meta):
        fields = PrivateOrganizationBlogPostWriteSerializer.Meta.fields
        read_only_fields = fields
