from datetime import date
from django.db import models


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
        self.rainforest_response = rainforest_response

    def get_amazon_product(self):
        product_data = self.rainforest_response["product"]

        assert product_data

        return AmazonProduct.objects.create(
            **{
                "asin": product_data["asin"],
                "title": product_data["title"],
                "link": product_data["link"],
                "description": product_data["description"],
                "image_url": product_data["main_image"]["link"],
                "price": product_data["buybox_winner"]["new_offers_from"]["value"],
            }
        )
