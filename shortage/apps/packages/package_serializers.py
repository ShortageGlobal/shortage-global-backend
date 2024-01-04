from django.db import transaction
from rest_framework import serializers
from shortage.helpers.serializers import AuthorizedUserOrNone
from shortage.apps.catalog.models import Product
from shortage.apps.catalog.serializers import (
    OrganizationPreviewSerializer,
    CampaignMinimalPreviewSerializer,
)
from .models import (
    Package,
    PackageItem,
    CorporateDonation,
    PackageType,
    PackageStatusLogEntry,
)
from .payments import generate_package_checkout_url


class PackageSerializer(serializers.ModelSerializer):
    organization = OrganizationPreviewSerializer(read_only=True)
    campaign = CampaignMinimalPreviewSerializer(read_only=True)

    class Meta:
        model = Package
        fields = [
            "uuid",
            "organization",
            "campaign",
            "delivery_company",
            "tracking_code",
            "created_at",
            "status",
            "type",
            "note",
            "need_tax_deduction",
            "tax_deduction_receipt",
        ]


class PackageNoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Package
        fields = [
            "note",
        ]


class ProductSlugRelatedField(serializers.SlugRelatedField):
    def get_queryset(self):
        organization = self.context["view"].organization
        return super().get_queryset().filter(organization=organization)


class PackageItemCreationSerializer(serializers.ModelSerializer):
    product = ProductSlugRelatedField(
        queryset=Product.objects.active(),
        slug_field="slug",
        allow_null=False,
        required=True,
    )
    quantity = serializers.IntegerField(
        min_value=1, max_value=2147483647, required=True
    )
    cart_item_uuid = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=False,
        default="",
        min_length=36,
        max_length=36,
    )

    class Meta:
        model = PackageItem
        fields = ["product", "quantity", "cart_item_uuid"]


class PackageCreationSerializer(serializers.ModelSerializer):
    campaign_uuid = serializers.UUIDField(required=False, allow_null=True)
    campaign_slug = serializers.SlugField(required=False, allow_null=True)
    items = PackageItemCreationSerializer(
        write_only=True, many=True, required=True, allow_empty=False
    )
    owner = serializers.HiddenField(default=AuthorizedUserOrNone())

    class Meta:
        model = Package
        fields = [
            "uuid",
            "campaign_uuid",
            "campaign_slug",
            "first_name",
            "last_name",
            "email",
            "phone_number",
            "need_tax_deduction",
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
            "owner",
            "items",
            "type",
            "checkout_url",
        ]
        read_only_fields = ["status"]

    def validate(self, attrs):
        type = attrs.get("type")
        items = attrs.get("items")

        errors = {}

        # Check tracking info is provided if needed
        if type == PackageType.SENT_BY_DONOR or not type:
            # require Delivery Company
            if not attrs.get("delivery_company"):
                errors["delivery_company"] = ["This field is required."]
            # require Tracking Code
            if not attrs.get("tracking_code"):
                errors["tracking_code"] = ["This field is required."]

        # Check all products are unique
        products_slug_set = set()
        for item in items:
            product = item["product"]

            product_slug = product.slug
            if product_slug in products_slug_set:
                errors["non_field_errors"] = (
                    "All items must be unique. Duplicated product: %s" % product.name
                )
                break
            products_slug_set.add(product_slug)

        # Raise validation errors if any
        if len(errors):
            raise serializers.ValidationError(errors)

        return super().validate(attrs)

    @transaction.atomic
    def create(self, validated_data):
        validated_items_data = validated_data.pop("items")

        organization = self.context["view"].organization
        validated_data["organization"] = organization

        campaign = None
        if hasattr(self.context["view"], "campaign"):
            campaign = self.context["view"].campaign
            validated_data["campaign"] = campaign

        # ignore these fields after validation
        validated_data.pop("campaign_slug", None)
        validated_data.pop("campaign_uuid", None)

        # create package
        package = Package.objects.create(**validated_data)
        # create package items

        items = [
            PackageItem(
                package=package,
                product=validated_item_data["product"],
                quantity=validated_item_data["quantity"],
                name=validated_item_data["product"].name,
                category=validated_item_data["product"].category,
                photo=validated_item_data["product"].photo,
                price=validated_item_data["product"].price,
                description=validated_item_data["product"].description,
            )
            for validated_item_data in validated_items_data
        ]
        PackageItem.objects.bulk_create(items)

        if package.type == PackageType.FUNDED_BY_DONOR:
            organization = self.context["view"].organization
            organization_slug = organization.slug
            organization_name = organization.name
            campaign_slug = campaign.slug if campaign else None
            campaign_uuid = campaign.uuid if campaign else None
            campaign_name = campaign.name if campaign else None
            cart_item_uuids = [item["cart_item_uuid"] for item in validated_items_data]

            package.checkout_url = generate_package_checkout_url(
                organization_slug,
                organization_name,
                package.uuid,
                items,
                cart_item_uuids,
                package.email,
                campaign_slug,
                campaign_uuid,
                campaign_name,
            )
            package.save()

        return package


class PackageStatusLogEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = PackageStatusLogEntry
        fields = ["status", "created_at"]
        read_only_fields = fields


class CorporateDonationSerializer(serializers.ModelSerializer):
    agreed_to_terms_of_use = serializers.BooleanField(required=True, write_only=True)

    class Meta:
        model = CorporateDonation
        fields = [
            "company_name",
            "department",
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
            "description",
            "quantity_description",
            "number_of_pallets",
            "estimated_value",
            "url",
            "photo",
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
