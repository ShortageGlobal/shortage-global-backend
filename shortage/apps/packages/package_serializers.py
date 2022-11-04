from django.db import transaction
from rest_framework import serializers
from shortage.helpers.serializers import AuthorizedUserOrNone
from shortage.apps.catalog.models import Product
from .models import Package, PackageItem, CorporateDonation, PackageType
from .payments import generate_package_checkout_url


class PackageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Package
        fields = [
            "uuid",
            "delivery_company",
            "tracking_code",
            "created_at",
            "status",
            "type",
        ]


class ProductSlugRelatedField(serializers.SlugRelatedField):
    def get_queryset(self):
        organization = self.context["view"].organization
        return super().get_queryset().filter(organization=organization)


class PackageItemCreationSerializer(serializers.ModelSerializer):
    product = ProductSlugRelatedField(
        queryset=Product.objects.public(),
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
    items = PackageItemCreationSerializer(
        write_only=True, many=True, required=True, allow_empty=False
    )
    owner = serializers.HiddenField(default=AuthorizedUserOrNone())

    class Meta:
        model = Package
        fields = [
            "uuid",
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
        items = attrs.get("items")

        # check all products are unique
        products_slug_set = set()
        for item in items:
            product_slug = item["product"].slug
            if product_slug in products_slug_set:
                raise serializers.ValidationError(
                    "All items must be unique. Duplicated product: %s" % product_slug
                )
            products_slug_set.add(product_slug)

        return super().validate(attrs)

    @transaction.atomic
    def create(self, validated_data):
        validated_items_data = validated_data.pop("items")

        # create package
        package = Package.objects.create(**validated_data)

        # create package items
        items = [
            PackageItem(
                package=package,
                product=validated_item_data["product"],
                quantity=validated_item_data["quantity"],
            )
            for validated_item_data in validated_items_data
        ]
        PackageItem.objects.bulk_create(items)

        if package.type == PackageType.FUNDED_BY_DONOR:
            organization = self.context["view"].organization
            organization_slug = organization.slug
            organization_name = organization.name
            cart_item_uuids = [item["cart_item_uuid"] for item in validated_items_data]

            package.checkout_url = generate_package_checkout_url(
                organization_slug,
                organization_name,
                package.uuid,
                items,
                cart_item_uuids,
                package.email,
            )
            package.save()

        return package


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
