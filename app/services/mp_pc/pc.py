"""Provider Component related functions"""

from logging import getLogger

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
