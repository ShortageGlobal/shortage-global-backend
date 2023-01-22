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


class GetProductByAsinViewSet(
    mixins.RetrieveModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet
):
    schema = AutoSchema(
        tags=["Products", "External Integration"],
    )

    permission_classes = [permissions.AllowAny]
    serializer_class = AmazonProductSerializer

    def get_object(self):
        asin = self.kwargs.get("asin")

        if not asin:
            raise NotFound()

        product = AmazonProduct.objects.valid_cached_products().filter(asin=asin)

        if not product:
            rainforest = RainforestWrapper()

            response = rainforest.send_request(asin=asin)

            if 200 == response.status_code:
                adapter = AmazonProductAdapter(rainforest_response=response.data)

                product = adapter.get_amazon_product()
                product.save()

        return product


class GetProductsByAmazonUrlViewSet(GetProductByAsinViewSet):
    schema = AutoSchema(
        tags=["Products", "External Integration"],
    )

    permission_classes = [permissions.AllowAny]
    serializer_class = AmazonProductSerializer

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
