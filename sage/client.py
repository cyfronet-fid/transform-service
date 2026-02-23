from typing import Any, Dict

import requests
from settings import settings


class AggregatorClient:
    def __init__(self):
        self.url = str(settings.aggregator_url)

        self.headers = {
            "x-api-key": settings.aggregator_api_key,
            "Content-Type": "application/json",
        }

    def build_query(self) -> Dict[str, Any]:
        return {
            "@context": {"@vocab": "https://w3id.org/edc"},
            "@type": "QuerySpec",
            "limit": settings.aggregator_api_limit,
        }

    def fetch_catalog(self) -> Dict[str, Any]:
        response = requests.post(
            self.url,
            headers=self.headers,
            json=self.build_query(),
            timeout=settings.request_timeout,
        )

        response.raise_for_status()
        return response.json()
