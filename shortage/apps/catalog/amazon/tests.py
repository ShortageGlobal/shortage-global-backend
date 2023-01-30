import base64

from rest_framework.test import APITestCase, APIRequestFactory, force_authenticate
from rest_framework.utils import json

from shortage.apps.catalog.amazon.models import AmazonProduct
from shortage.apps.catalog.amazon.views import (
    GetProductByAsinViewSet,
    GetProductsByAmazonUrlViewSet,
)
from shortage.helpers.test_utilities import create_test_user


class GetProductFromAmazonTestCase(APITestCase):
    def setUp(self) -> None:
        self.requestFactory = APIRequestFactory()
        self.user = create_test_user()

    def test_get_products_by_asin(self):
        request = self.requestFactory.get("", format="json")
        force_authenticate(request, user=self.user)
        response = GetProductByAsinViewSet.as_view({"get": "retrieve"})(
            request, asin="B000YDDF6O"
        )

        self.assertEqual(response.status_code, 200)

        content = json.loads(response.render().content)

        self.assertEqual(content["asin"], "B000YDDF6O")
        self.assertEqual(
            content["title"],
            "Baby Einstein Take Along Tunes Musical Toy, Ages 3 months +",
        )
        self.assertEqual(
            content["link"],
            "https://www.amazon.com/Baby-Einstein-Along-Tunes-Musical/dp/B000YDDF6O",
        )
        self.assertEqual(
            content["description"],
            "PRODUCT DESCRIPTION \n Baby Einstein take along tunes. \n\n FROM THE MANUFACTURER \n Promote music appreciation and auditory development by introducing your little one to baby-friendly versions of classical masterpieces by Mozart, Vivaldi, Chopin and Rossini with the Baby Einstein take along Tunes. A large, easy to press button allows your baby to toggle through 7 high quality and enjoyable classical melodies at home, or for on-the-go fun. This baby's version of an MP3 player has colorful lights that dance across the screen to enhance each entertaining melody and promote visual perception.",
        )
        self.assertEqual(
            content["image_url"], "https://m.media-amazon.com/images/I/81s+p-98uyL.jpg"
        )
        self.assertEqual(content["price"], "9.99")

        # Check that object is now in cache
        product = AmazonProduct.objects.valid_cached_products().filter(
            asin=content["asin"]
        )

        self.assertNotEqual(product, None)

    def test_get_products_by_url(self):
        url = base64.urlsafe_b64encode(
            b"https://www.amazon.com/Baby-Einstein-Along-Tunes-Musical/dp/B000YDDF6O"
        )
        url = url.decode()

        request = self.requestFactory.get("", format="json")
        force_authenticate(request, user=self.user)
        response = GetProductsByAmazonUrlViewSet.as_view({"get": "retrieve"})(
            request,
            url=url,
        )

        self.assertEqual(response.status_code, 200)

        content = json.loads(response.render().content)

        self.assertEqual(content["asin"], "B000YDDF6O")
        self.assertEqual(
            content["title"],
            "Baby Einstein Take Along Tunes Musical Toy, Ages 3 months +",
        )
        self.assertEqual(
            content["link"],
            "https://www.amazon.com/Baby-Einstein-Along-Tunes-Musical/dp/B000YDDF6O",
        )
        self.assertEqual(
            content["description"],
            "PRODUCT DESCRIPTION \n Baby Einstein take along tunes. \n\n FROM THE MANUFACTURER \n Promote music appreciation and auditory development by introducing your little one to baby-friendly versions of classical masterpieces by Mozart, Vivaldi, Chopin and Rossini with the Baby Einstein take along Tunes. A large, easy to press button allows your baby to toggle through 7 high quality and enjoyable classical melodies at home, or for on-the-go fun. This baby's version of an MP3 player has colorful lights that dance across the screen to enhance each entertaining melody and promote visual perception.",
        )
        self.assertEqual(
            content["image_url"],
            "https://m.media-amazon.com/images/I/81s+p-98uyL.jpg",
        )
        self.assertEqual(content["price"], "9.99")

        # Check that object is now in cache
        product = AmazonProduct.objects.valid_cached_products().filter(
            asin=content["asin"]
        )

        self.assertNotEqual(product, None)
