import json
from datetime import date

from auditlog.registry import auditlog
from django.db import models
from rest_framework.exceptions import NotFound


class AmazonProductsManager(models.Manager):
    def valid_cached_products(self):
        return self.all().filter(
            created_at=date.today(),
        )


class AmazonProduct(models.Model):
    asin = models.CharField(max_length=10, primary_key=True)

    title = models.TextField(max_length=2000, null=False, blank=False)
    description = models.TextField(max_length=2000, null=True, blank=True)
    price = models.DecimalField(
        null=False, blank=False, decimal_places=2, max_digits=10
    )

    link = models.URLField(max_length=255, null=False, blank=False)
    image_url = models.URLField(max_length=255, null=True, blank=True)

    created_at = models.DateField(auto_now_add=True)

    objects = AmazonProductsManager()


class AmazonProductAdapter:
    rainforest_response = None

    def __init__(self, rainforest_response):

        if type(rainforest_response) is dict:
            self.rainforest_response = rainforest_response
        else:
            self.rainforest_response = json.loads(rainforest_response)

    def get_amazon_product(self):
        if not self.rainforest_response["request_info"]["success"]:
            raise NotFound()

        product_data = self.rainforest_response["product"]

        assert product_data

        price = "0.00"

        if product_data.get("price"):
            price = product_data["price"]["value"]
        elif product_data.get("buybox_winner"):
            buybox_winner = product_data["buybox_winner"]

            if buybox_winner.get("price"):
                price = buybox_winner["price"]["value"]
            elif buybox_winner.get("new_offers_from"):
                price = buybox_winner["new_offers_from"]["price"]["value"]
            elif buybox_winner.get("secondary_buybox"):
                price = buybox_winner["secondary_buybox"]["price"]["value"]

        elif product_data.get("more_buying_choices"):
            price = product_data["more_buying_choices"][0]["price"]["value"]

        return AmazonProduct.objects.create(
            **{
                "asin": product_data.get("asin"),
                "title": product_data.get("title"),
                "link": product_data.get("link"),
                "description": product_data.get("description"),
                "image_url": product_data.get("main_image").get("link"),
                "price": price,
            }
        )


auditlog.register(AmazonProduct)
