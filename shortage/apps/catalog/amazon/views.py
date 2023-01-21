import base64

from rest_framework.response import Response
from rest_framework import (
    viewsets,
    mixins,
    permissions,
)
from rest_framework.schemas.openapi import AutoSchema

from shortage.apps.catalog.amazon.models import AmazonProduct, AmazonProductsManager
from shortage.apps.catalog.amazon.rainforest import RainforestWrapper
from shortage.apps.catalog.amazon.serializers import AmazonProductSerializer


def create_product_description_from_rainforest_product_data(product_data):
    assert product_data

    return {
        "asin": product_data["asin"],
        "title": product_data["title"],
        "link": product_data["link"],
        "description": product_data["description"],
        "image_url": product_data["main_image"]["link"],
        "price": product_data["buybox_winner"]["new_offers_from"]["value"],
    }


class GetProductByAsinViewSet(
    mixins.RetrieveModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet
):
    schema = AutoSchema(
        tags=["Products", "External Integration"],
    )

    permission_classes = [permissions.AllowAny]
    serializer_class = AmazonProductSerializer

    def get_object(self):
        product = AmazonProduct.objects.valid_cached_products().filter(
            asin=self.kwargs["asin"]
        )

        if not product:
            rainforest = RainforestWrapper()

            response = rainforest.send_request(asin=self.kwargs["asin"])

            if 200 == response.status_code:
                response_object = (
                    create_product_description_from_rainforest_product_data(
                        response.data["product"]
                    )
                )

                product = AmazonProduct.objects.create(**response_object)
                product.save()

        return product


class GetProductsByAmazonUrlViewSet(GetProductByAsinViewSet):
    schema = AutoSchema(
        tags=["Products", "External Integration"],
    )

    permission_classes = [permissions.AllowAny]
    serializer_class = AmazonProductSerializer

    def get_object(self):
        rainforest = RainforestWrapper()

        amazon_url = base64.urlsafe_b64decode(str.encode(self.kwargs["url"])).decode()
        asin = rainforest.get_asin_from_url(amazon_url)

        assert asin

        self.kwargs["asin"] = asin

        return super().get_object()
