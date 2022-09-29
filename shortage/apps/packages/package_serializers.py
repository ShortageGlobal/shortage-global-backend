from django.db import transaction
from rest_framework import serializers
from shortage.apps.packages.payments import generate_package_checkout_url
from shortage.helpers.serializers import AuthorizedUserOrNone
from shortage.apps.catalog.models import Product
from .models import Package, PackageItem, CorporateDonation, PackageType, PackageStatus


class PackageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Package
        fields = [
            "uuid",
            "delivery_company",
            "tracking_code",
            "created_at",
            "status",
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

    class Meta:
        model = PackageItem
        fields = ["product", "quantity"]


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
            PackageItem(package=package, **validated_item_data)
            for validated_item_data in validated_items_data
        ]
        PackageItem.objects.bulk_create(items)

        if package.type == PackageType.FUNDED_BY_DONOR:
            organization = self.context["view"].organization
            organization_slug = organization.slug

            total_price = 0
            for item in items:
                total_price += item.product.price

            package.checkout_url = generate_package_checkout_url(
                organization_slug,
                package.uuid,
                "Donation for %s" % organization.name,
                total_price,
                package.email,
            )
            package.save()

        return package


class CorporateDonationSerializer(serializers.ModelSerializer):
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
        ]
