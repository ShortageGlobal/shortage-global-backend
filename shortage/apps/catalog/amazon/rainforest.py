import requests.models
import re

from shortage import settings


class RainforestWrapper:
    api_key = settings.RAINFOREST_API_KEY
    rainforest_api_url = "https://api.rainforestapi.com/request"
    amazon_domain = "amazon.com"

    def send_request(self, **kwargs):
        params = {
            "api_key": self.api_key,
            "type": "product",
            "amazon_domain": self.amazon_domain,
            **kwargs,
        }

        # Longer timeout because Amazon requests take 30+ seconds sometimes
        return requests.get(self.rainforest_api_url, params, timeout=60)

    def get_asin_from_url(self, url):
        match = re.search(r"/[dg]p/([^/]+)", url, flags=re.IGNORECASE)

        if match:
            return match.group(1)

        return None
