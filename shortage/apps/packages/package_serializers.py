from django.db import transaction
from rest_framework import serializers
from rest_framework.fields import CurrentUserDefault
from shortage.apps.catalog.models import Product
from .models import Package, PackageItem


class AuthorizedUserOrNone(CurrentUserDefault):
    def __call__(self, serializer_field):
        user = serializer_field.context["request"].user
        if user.is_authenticated:
            return user

        return None


class ProductSlugRelatedField(serializers.SlugRelatedField):
    def get_queryset(self):
        organization = self.context["view"].organization
        return super().get_queryset().filter(organization=organization)


class PackageItemSerializer(serializers.ModelSerializer):
    product = ProductSlugRelatedField(
        queryset=Product.objects.all(),
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
        read_only_fields = fields


class PackageSerializer(serializers.ModelSerializer):
    items = PackageItemSerializer(
        write_only=True, many=True, required=False, allow_empty=True
    )

    class Meta:
        model = Package
        fields = [
            "uuid",
            "created_at",
            "full_name",
            "email",
            "phone_number",
            "delivery_company",
            "tracking_code",
            "note",
            "status",
            "items",
        ]
        read_only_fields = fields


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
            "created_at",
            "full_name",
            "email",
            "phone_number",
            "delivery_company",
            "tracking_code",
            "note",
            "status",
            "photo",
            "owner",
            "items",
        ]
        read_only_fields = ["uuid", "status", "created_at"]

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

        package = Package.objects.create(**validated_data)

        # create package items
        items = [
            PackageItem(package=package, **validated_item_data)
            for validated_item_data in validated_items_data
        ]
        PackageItem.objects.bulk_create(items)

        return package
