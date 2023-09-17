from django.db import transaction
from rest_framework import serializers, exceptions
from shortage.helpers.serializers import AuthorizedUserOrNone
from shortage.apps.catalog.models import Product, Campaign
from shortage.apps.catalog.serializers import (
    OrganizationPreviewSerializer,
    CampaignMinimalPreviewSerializer,
)
from .models import Cart, CartItem


class CartItemProductSerializer(serializers.ModelSerializer):
    organization = OrganizationPreviewSerializer()
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
    product = CartItemProductSerializer()
    campaign = CampaignMinimalPreviewSerializer()
    quantity = serializers.IntegerField(min_value=1, max_value=2147483647)

    class Meta:
        model = CartItem
        fields = ["uuid", "product", "campaign", "quantity", "created_at"]


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
    campaign_slug = serializers.SlugField(write_only=True, required=False)
    campaign_uuid = serializers.UUIDField(write_only=True, required=False)
    quantity = serializers.IntegerField(
        min_value=1, max_value=2147483647, required=True, write_only=True
    )

    class Meta:
        model = CartItem
        fields = [
            "uuid",
            "product_slug",
            "organization_slug",
            "campaign_slug",
            "campaign_uuid",
            "quantity",
        ]

    def validate(self, attrs):
        product_slug = attrs.get("product_slug")
        organization_slug = attrs.get("organization_slug")
        campaign_slug = attrs.get("campaign_slug")
        campaign_uuid = attrs.get("campaign_uuid")

        # if we create/update/delete a CartItem of the existing Cart, not creating a new Cart,
        # there will be 'cart_pk' in the context
        cart_pk = self.context.get("cart_pk")  # Cart pk
        pk = self.context.get("pk")  # CartItem pk
        if cart_pk is not None:
            # check the cart exists
            if not Cart.objects.filter(pk=cart_pk).exists():
                raise exceptions.NotFound()

            queryset = CartItem.objects.filter(
                cart=cart_pk,
                product__slug=product_slug,
                product__organization__slug=organization_slug,
            )

            # check the product/organization/campaign triplet is unique for the given cart
            if campaign_slug and campaign_uuid:
                if (
                    queryset.filter(
                        campaign__slug=campaign_slug,
                        campaign__uuid=campaign_uuid,
                    )
                    .exclude(pk=pk)
                    .exists()
                ):
                    raise serializers.ValidationError(
                        "Cart already includes this product for the given campaign"
                    )
            # check the product/organization pair is unique for the given cart
            elif queryset.filter(campaign=None).exclude(pk=pk).exists():
                raise serializers.ValidationError("Cart already includes this product")

        # check product with the given slug and the given organization/campaign exists
        queryset = Product.objects.active().filter(
            slug=product_slug, organization__slug=organization_slug
        )

        if campaign_slug and campaign_uuid:
            if not queryset.filter(
                campaign__slug=campaign_slug,
                campaign__uuid=campaign_uuid,
            ).exists():
                raise serializers.ValidationError(
                    'Product with "%s" slug, "%s" organization slug, "%s" campaign slug, and "%s" campaign uuid does not exist'
                    % (product_slug, organization_slug, campaign_slug, campaign_uuid)
                )
        elif not queryset.exists():
            raise serializers.ValidationError(
                'Product with "%s" slug and "%s" organization slug does not exist'
                % (product_slug, organization_slug)
            )

        return super().validate(attrs)

    def create(self, validated_data):
        product_slug = validated_data.pop("product_slug")
        organization_slug = validated_data.pop("organization_slug")
        campaign_uuid = validated_data.pop("campaign_uuid", None)
        quantity = validated_data.pop("quantity")
        cart_pk = self.context["cart_pk"]

        cart_params = {
            "cart_id": cart_pk,
            "product": Product.objects.active().get(
                slug=product_slug,
                organization__slug=organization_slug,
            ),
            "quantity": quantity,
        }

        if campaign_uuid:
            cart_params["campaign"] = Campaign.objects.active().get(pk=campaign_uuid)

        cart_item = CartItem.objects.create(**cart_params)

        return cart_item


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)

    class Meta:
        model = Cart
        fields = [
            "uuid",
            "created_at",
            "items",
            "agreed_to_terms_of_use",
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
        ]


class CartCreationSerializer(serializers.ModelSerializer):
    items = CartItemCreationSerializer(
        write_only=True, many=True, required=False, allow_empty=True
    )
    owner = serializers.HiddenField(default=AuthorizedUserOrNone())

    class Meta:
        model = Cart
        fields = ["items", "owner", "uuid"]

    def validate(self, attrs):
        items = attrs.get("items", [])

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
        validated_items_data = (
            validated_data.pop("items") if "items" in validated_data else []
        )

        # create cart
        cart = Cart.objects.create(**validated_data)

        # create package items
        items = [
            CartItem(
                cart=cart,
                quantity=validated_item_data["quantity"],
                product=Product.objects.active().get(
                    slug=validated_item_data["product_slug"],
                    organization__slug=validated_item_data["organization_slug"],
                ),
            )
            for validated_item_data in validated_items_data
        ]
        CartItem.objects.bulk_create(items)

        return cart


class CartUpdateSerializer(serializers.ModelSerializer):
    agreed_to_terms_of_use = serializers.BooleanField(required=True)

    class Meta:
        model = Cart
        fields = [
            "agreed_to_terms_of_use",
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
        ]

    def validate(self, attrs):
        errors = {}

        # Required fields
        required_fields = ["email"]
        for field in required_fields:
            if not attrs.get(field):
                errors[field] = ["This field is required."]

        # Require fields if tax deduction is requested
        required_for_tax_deduction_fields = [
            "first_name",
            "last_name",
            "phone_number",
            "address_line1",
            "city",
            "state_province_region",
            "zip",
            "country",
        ]
        need_tax_deduction = attrs.get("need_tax_deduction")
        if need_tax_deduction is True:
            for field in required_for_tax_deduction_fields:
                if not attrs.get(field):
                    errors[field] = ["This field is required."]

        # Raise validation errors if any
        if len(errors):
            raise serializers.ValidationError(errors)

        return super().validate(attrs)

    def validate_agreed_to_terms_of_use(self, value):
        if not value:
            raise serializers.ValidationError(
                "You must agree to the Terms of Use Policy."
            )
        return value
