import sys
import requests
from rest_framework.response import Response
import re

from shortage import settings
from shortage.apps.catalog.amazon.rainforest_sample_response import (
    RAINFOREST_SAMPLE_RESPONSE,
)


class RainforestWrapper:
    api_key = settings.RAINFOREST_API_KEY
    rainforest_api_url = "https://api.rainforestapi.com/request"
    amazon_domain = "amazon.com"

    def send_request(self, **kwargs):
        # Return hardcoded response data to save API credits when running unit tests
        if self.is_test_mode():
            return Response(
                status=200, data=RAINFOREST_SAMPLE_RESPONSE, content_type="json"
            )

        params = {
            "api_key": self.api_key,
            "type": "product",
            "amazon_domain": self.amazon_domain,
            **kwargs,
        }

        return requests.get(self.rainforest_api_url, params)

    def get_asin_from_url(self, url):
        match = re.search(r"/[dg]p/([^/]+)", url, flags=re.IGNORECASE)

        if match:
            return match.group(1)

        return None

    def is_test_mode(self):
        if len(sys.argv) > 1 and "manage.py" == sys.argv[0] and "test" == sys.argv[1]:
            return True

        return False
