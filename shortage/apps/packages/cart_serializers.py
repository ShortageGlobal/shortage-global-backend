from django.db import transaction
from django.http import Http404
from rest_framework import serializers
from shortage.apps.catalog.models import Product
from shortage.apps.catalog.serializers import ProductOrganizationPreviewSerializer
from .models import Cart, CartItem


class ProductCartItemSerializer(serializers.ModelSerializer):
    organization = ProductOrganizationPreviewSerializer()
    photo = serializers.ImageField(source="medium_photo")

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
            "organization",
        ]


class CartItemSerializer(serializers.ModelSerializer):
    product = ProductCartItemSerializer()
    quantity = serializers.IntegerField(min_value=1, max_value=2147483647)

    class Meta:
        model = CartItem
        fields = ["uuid", "product", "quantity", "created_at"]


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)

    class Meta:
        model = Cart
        fields = [
            "uuid",
            "created_at",
            "items",
        ]


class CartItemUpdateSerializer(serializers.ModelSerializer):
    quantity = serializers.IntegerField(
        min_value=1, max_value=2147483647, required=True, write_only=True
    )

    class Meta:
        model = CartItem
        fields = ["uuid", "quantity"]


class CartItemCreationSerializer(serializers.ModelSerializer):
    product_slug = serializers.SlugField(write_only=True)
    organization_slug = serializers.SlugField(write_only=True)
    quantity = serializers.IntegerField(
        min_value=1, max_value=2147483647, required=True, write_only=True
    )

    class Meta:
        model = CartItem
        fields = ["uuid", "product_slug", "organization_slug", "quantity"]

    def validate(self, attrs):
        product_slug = attrs.get("product_slug")
        organization_slug = attrs.get("organization_slug")

        # if we create/update/delete a CartItem of the existing Cart, there will be 'cart_pk' in the context
        cart_pk = self.context.get("cart_pk")  # Cart pk
        pk = self.context.get("pk")  # CartItem pk
        if cart_pk is not None:
            # check the cart exists
            if not Cart.objects.filter(pk=cart_pk).exists():
                raise Http404()

            # check the product/organization pair is unique for the given cart
            if (
                CartItem.objects.filter(
                    cart=cart_pk,
                    product__slug=product_slug,
                    product__organization__slug=organization_slug,
                )
                .exclude(pk=pk)
                .exists()
            ):
                raise serializers.ValidationError("Cart already includes this product")

        # check product with the given slug and the given organization slug exists
        if (
            not Product.objects.public()
            .filter(slug=product_slug, organization__slug=organization_slug)
            .exists()
        ):
            raise serializers.ValidationError(
                'Product with "%s" slug and "%s" organization slug does not exist'
                % (product_slug, organization_slug)
            )

        return super().validate(attrs)

    def create(self, validated_data):
        product_slug = validated_data.pop("product_slug")
        organization_slug = validated_data.pop("organization_slug")
        quantity = validated_data.pop("quantity")
        cart_pk = self.context["cart_pk"]

        cart_item = CartItem.objects.create(
            cart_id=cart_pk,
            product=Product.objects.public().get(
                slug=product_slug, organization__slug=organization_slug
            ),
            quantity=quantity,
        )

        return cart_item


class CartCreationSerializer(serializers.ModelSerializer):
    items = CartItemCreationSerializer(
        write_only=True, many=True, required=True, allow_empty=False
    )
    owner = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Cart
        fields = ["items", "owner", "uuid"]

    def validate(self, attrs):
        items = attrs.get("items")

        # check all product_slug and organization_slug pairs are unique
        slug_pairs_set = set()
        for item in items:
            product_slug = item["product_slug"]
            organization_slug = item["organization_slug"]
            slug_pair = product_slug + organization_slug
            if slug_pair in slug_pairs_set:
                raise serializers.ValidationError(
                    'All product_slug/organization_slug pairs must be unique. Duplicated pair: "%s" and "%s"'
                    % (product_slug, organization_slug)
                )
            slug_pairs_set.add(slug_pair)

        return super().validate(attrs)

    @transaction.atomic
    def create(self, validated_data):
        validated_items_data = validated_data.pop("items")

        # create cart
        cart = Cart.objects.create(**validated_data)

        # create package items
        items = [
            CartItem(
                cart=cart,
                quantity=validated_item_data["quantity"],
                product=Product.objects.public().get(
                    slug=validated_item_data["product_slug"],
                    organization__slug=validated_item_data["organization_slug"],
                ),
            )
            for validated_item_data in validated_items_data
        ]
        CartItem.objects.bulk_create(items)

        return cart
