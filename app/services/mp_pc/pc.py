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


def map_nodes(data: dict[str, Any], keep_node_pid: bool = False) -> dict[str, Any]:
    """Safely replace selected node coded values with their facet labels."""
    node_mapping = get_facet_mapping(data, "node")

    map_node_values(data, node_mapping, keep_node_pid)

    return data


def map_licenses(data: dict[str, Any]) -> dict[str, Any]:
    """Safely replace license identifiers with their facet labels."""
    license_mapping = get_facet_mapping(data, "license")

    map_license_values(data, license_mapping)

    return data


def map_resource_owners(data: dict[str, Any]) -> dict[str, Any]:
    """Add provider label based on resource_owner facet mapping."""
    resource_owner_mapping = get_facet_mapping(data, "resource_owner")

    map_resource_owner_values(data, resource_owner_mapping)

    return data


def map_resource_organisations(data: dict[str, Any]) -> dict[str, Any]:
    """Add label based on facet mapping."""
    resource_owner_mapping = get_facet_mapping(data, "resource_owner")

    map_resource_organisation_values(data, resource_owner_mapping)

    return data


def map_catalogues(data: dict[str, Any]) -> dict[str, Any]:
    """Add catalogue label based on catalogue facet mapping."""
    catalogue_mapping = get_facet_mapping(data, "catalogue_id")

    map_catalogue_values(data, catalogue_mapping)

    return data


def get_facet_mapping(data: dict[str, Any], field: str) -> dict[str, str]:
    """Build a value-to-label mapping from Provider Component facets."""
    for facet in data.get("facets", []):
        if facet.get("field") != field:
            continue

        return {
            value["value"]: value["label"]
            for value in facet.get("values", [])
            if value.get("value") and value.get("label")
        }

    return {}


def map_node_values(
    data: dict[str, Any], node_mapping: dict[str, str], keep_node_pid: bool
) -> None:
    """Map node PID values to labels, optionally preserving the raw nodePID."""
    if not node_mapping:
        return

    for item in data.get("results", []):
        original_node = item.get("nodePID")
        if isinstance(original_node, str) and original_node in node_mapping:
            item["node"] = node_mapping[original_node]
            if not keep_node_pid:
                del item["nodePID"]


def map_license_values(data: dict[str, Any], license_mapping: dict[str, str]) -> None:
    """Map license identifiers to labels for string and nested license fields."""
    if not license_mapping:
        return

    for item in data.get("results", []):
        license_value = item.get("license")

        if isinstance(license_value, str) and license_value in license_mapping:
            item["license"] = license_mapping[license_value]
            continue

        if not isinstance(license_value, dict):
            continue

        license_name = license_value.get("licenseName")
        if isinstance(license_name, str) and license_name in license_mapping:
            license_value["licenseName"] = license_mapping[license_name]


def map_resource_owner_values(
    data: dict[str, Any],
    resource_owner_mapping: dict[str, str],
) -> None:
    """Map resource owner PID to provider label."""
    if not resource_owner_mapping:
        return

    for item in data.get("results", []):
        resource_owner = item.get("resourceOwner")

        if isinstance(resource_owner, str) and resource_owner in resource_owner_mapping:
            item["provider"] = resource_owner_mapping[resource_owner]


def map_resource_organisation_values(
    data: dict[str, Any],
    resource_owner_mapping: dict[str, str],
) -> None:
    """Map resource organisation/owner PID to label."""
    if not resource_owner_mapping:
        return

    for item in data.get("results", []):
        resource_owner = item.get("resourceOwner")

        if isinstance(resource_owner, str) and resource_owner in resource_owner_mapping:
            item["resourceOwner"] = resource_owner_mapping[resource_owner]


def map_catalogue_values(
    data: dict[str, Any],
    resource_owner_mapping: dict[str, str],
) -> None:
    """Map catalogue to label."""
    if not resource_owner_mapping:
        return

    for item in data.get("results", []):
        resource_owner = item.get("catalogue_id")

        if isinstance(resource_owner, str) and resource_owner in resource_owner_mapping:
            item["catalogue"] = resource_owner_mapping[resource_owner]
