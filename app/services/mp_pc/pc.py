"""Provider Component related functions"""

from logging import getLogger
from typing import Any

import requests

logger = getLogger(__name__)


def get_access_token_from_refresh_token(
    refresh_token: str,
    client_id: str,
    token_url: str,
    scope: str = "openid email profile entitlements",
    timeout: int = 10,
) -> str | None:
    """
    Exchanges a refresh token for an access token using the Keycloak token endpoint.

    Args:
        refresh_token (str): The refresh token to exchange.
        client_id (str): The client ID registered with Keycloak.
        token_url (str): The token endpoint URL.
        scope (str): Optional scopes to include.
        timeout (int): Timeout for the request in seconds.

    Returns:
        str | None: The new access token if successful, otherwise None.
    """
    try:
        payload = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": client_id,
            "scope": scope,
        }

        response = requests.post(token_url, data=payload, timeout=timeout)
        response.raise_for_status()

        token_data = response.json()
        return token_data.get("access_token")

    except requests.RequestException as err:
        logger.error(f"Failed to get access token from refresh token: {err}")
        return None


def map_nodes(data: dict[str, Any]) -> dict[str, Any]:
    """Safely replace 'node' values in results with their corresponding labels from facets."""
    node_mapping = {}

    # Build mapping from facets
    for facet in data.get("facets", []):
        if facet.get("field") == "node":
            for value in facet.get("values", []):
                node_value = value.get("value")
                node_label = value.get("label")
                if node_value and node_label:
                    node_mapping[node_value] = node_label
            break  # No need to check other facets once we found 'node'

    # Only apply mapping if any node labels were found
    if node_mapping:
        for item in data.get("results", []):
            original_node = item.get("node")
            if isinstance(original_node, str) and original_node in node_mapping:
                item["node"] = node_mapping[original_node]

    return data
