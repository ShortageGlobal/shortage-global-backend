import base64

from rest_framework import (
    viewsets,
    mixins,
    permissions,
)
from rest_framework.exceptions import NotFound
from rest_framework.schemas.openapi import AutoSchema

from shortage.apps.catalog.amazon.models import AmazonProduct, AmazonProductAdapter
from shortage.apps.catalog.amazon.rainforest import RainforestWrapper
from shortage.apps.catalog.amazon.serializers import AmazonProductSerializer


class PrivateProductByAsinViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    schema = AutoSchema(
        tags=["Private", "Products", "External Integration"],
    )

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = AmazonProductSerializer
    lookup_field = "asin"

    def get_object(self):
        asin = self.kwargs.get("asin")

        if not asin:
            raise NotFound()

        product = None
        cached_product = AmazonProduct.objects.valid_cached_products().filter(asin=asin)

        if cached_product.exists():
            product = cached_product.get()
        else:
            rainforest = RainforestWrapper()

            response = rainforest.send_request(asin=asin)
            response.raise_for_status()

            if 200 == response.status_code:
                adapter = AmazonProductAdapter(rainforest_response=response.json())

                product = adapter.get_amazon_product()
                product.save()

        return product


class PrivateProductByAmazonUrlViewSet(PrivateProductByAsinViewSet):
    schema = AutoSchema(
        tags=["Private", "Products", "External Integration"],
    )

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = AmazonProductSerializer
    lookup_field = "url"

    def get_object(self):
        url = self.kwargs.get("url")

        if not url:
            raise NotFound()

        rainforest = RainforestWrapper()

        amazon_url = base64.urlsafe_b64decode(str.encode(url)).decode()
        asin = rainforest.get_asin_from_url(amazon_url)

        if not asin:
            raise NotFound()

        self.kwargs["asin"] = asin

        return super().get_object()
