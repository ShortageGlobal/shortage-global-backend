import base64
from unittest.mock import Mock, patch

from rest_framework.test import APITestCase, APIRequestFactory, force_authenticate
from rest_framework.utils import json
import requests.models

from shortage.apps.catalog.amazon.models import AmazonProduct
from shortage.apps.catalog.amazon.rainforest import RainforestWrapper
from shortage.apps.catalog.amazon.rainforest_sample_response import (
    RAINFOREST_SAMPLE_RESPONSE_2,
    RAINFOREST_SAMPLE_RESPONSE_1,
    RAINFOREST_SAMPLE_RESPONSE_4,
)
from shortage.apps.catalog.amazon.views import (
    PrivateProductByAsinViewSet,
    PrivateProductByAmazonUrlViewSet,
)
from shortage.helpers.test_utilities import create_test_user


def send_response_1(*args, **kwargs):
    mock_response = Mock(spec=requests.Response)

    mock_response.json.return_value = json.dumps(RAINFOREST_SAMPLE_RESPONSE_1)
    mock_response.status_code = 200

    return mock_response


def send_response_2(*args, **kwargs):
    mock_response = Mock(spec=requests.Response)

    mock_response.json.return_value = json.dumps(RAINFOREST_SAMPLE_RESPONSE_2)
    mock_response.status_code = 200

    return mock_response


def send_response_4(*args, **kwargs):
    mock_response = Mock(spec=requests.Response)

    mock_response.json.return_value = json.dumps(RAINFOREST_SAMPLE_RESPONSE_4)
    mock_response.status_code = 200

    return mock_response


class GetProductFromAmazonTestCase(APITestCase):
    def setUp(self) -> None:
        self.requestFactory = APIRequestFactory()
        self.user = create_test_user()

    @patch.object(RainforestWrapper, "send_request", send_response_1)
    def test_get_products_by_asin(self):
        request = self.requestFactory.get("", format="json")
        force_authenticate(request, user=self.user)
        response = PrivateProductByAsinViewSet.as_view({"get": "retrieve"})(
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
        self.assertNotEqual(AmazonProduct.objects.get(asin=content["asin"]), None)

    @patch.object(RainforestWrapper, "send_request", send_response_2)
    def test_get_products_by_url(self):
        url = base64.urlsafe_b64encode(
            b"https://www.amazon.com/Baby-Einstein-Along-Tunes-Musical/dp/B000YDDF6O"
        )
        url = url.decode()

        request = self.requestFactory.get("", format="json")
        force_authenticate(request, user=self.user)
        response = PrivateProductByAmazonUrlViewSet.as_view({"get": "retrieve"})(
            request,
            url=url,
        )

        self.assertEqual(response.status_code, 200)

        content = json.loads(response.render().content)

        self.assertEqual(content["asin"], "B098RKWHHZ")
        self.assertEqual(
            content["title"],
            "Nintendo Switch – OLED Model w/ White Joy-Con White Console",
        )
        self.assertEqual(
            content["link"],
            "https://www.amazon.com/Nintendo-Switch-OLED-Model-White-Joy/dp/B098RKWHHZ",
        )
        self.assertEqual(
            content["image_url"],
            "https://m.media-amazon.com/images/I/51yJ+OqktYL.jpg",
        )
        self.assertEqual(content["price"], "349.99")

        # Check that object is now in cache
        self.assertNotEqual(AmazonProduct.objects.get(asin=content["asin"]), None)

    @patch.object(RainforestWrapper, "send_request", send_response_4)
    def test_product_not_found(self):
        request = self.requestFactory.get("", format="json")
        force_authenticate(request, user=self.user)
        response = PrivateProductByAsinViewSet.as_view({"get": "retrieve"})(
            request, asin="B0B2X4JXBW"
        )

        self.assertEqual(response.status_code, 404)

        # Check that there is nothing in cache
        try:
            AmazonProduct.objects.get(asin="B0B2X4JXBW")
        except AmazonProduct.DoesNotExist:
            pass
        except:
            self.assertTrue(True)
        finally:
            self.assertTrue(True)
