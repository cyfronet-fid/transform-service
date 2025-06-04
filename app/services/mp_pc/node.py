from logging import getLogger
from typing import Optional

import requests

logger = getLogger(__name__)

# Internal singleton cache
_node_id_name_mapping_cache: Optional[dict[str, str]] = None


def get_node_id_name_mapping(url: str) -> Optional[dict[str, str]]:
    """
    Fetches a list of node entries from a given URL and constructs a mapping of node IDs to their names,
    using a singleton pattern to cache the result for the duration of the process.

    This function sends a GET request to the provided URL expecting a JSON response with a list of dictionaries,
    each representing a node. It returns a dictionary mapping each node's 'id' to its 'name'.

    The result is cached after the first call and reused for subsequent calls. To clear the cache between
    Celery tasks or processes, use the `reset_node_id_name_mapping_cache()` function.

    Parameters:
    ----------
    url : str
        The endpoint URL to fetch the node data from. The URL must return a JSON array where each item
        contains 'id' and 'name' fields.

    Returns:
    -------
    Optional[Dict[str, str]]
        A dictionary where the keys are node IDs and the values are node names.
        Returns None if the request fails, the response is not JSON, or the list is empty.

    Raises:
    ------
    None. All exceptions are caught and logged internally.
    """
    global _node_id_name_mapping_cache

    if _node_id_name_mapping_cache is not None:
        return _node_id_name_mapping_cache

    try:
        response = requests.get(url, headers={"accept": "application/json"}, timeout=10)
        response.raise_for_status()
        data = response.json()

        if not isinstance(data, list) or not data:
            logger.warning("Received empty or invalid data format.")
            return None

        mapping = {
            item["id"]: item["name"] for item in data if "id" in item and "name" in item
        }
        if mapping:
            _node_id_name_mapping_cache = mapping
            return mapping
        else:
            logger.warning(
                f"No valid node entries found in the response for url: {url}"
            )
            return None

    except requests.RequestException as e:
        logger.error(f"HTTP request failed: {e}")
    except ValueError as e:
        logger.error(f"Failed to parse JSON: {e}")
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")

    return None


def reset_node_id_name_mapping_cache():
    """
    Clears the singleton cache storing the node ID to name mapping.
    Call this at the end of a Celery task to ensure fresh data is fetched next time.
    """
    global _node_id_name_mapping_cache
    _node_id_name_mapping_cache = None
