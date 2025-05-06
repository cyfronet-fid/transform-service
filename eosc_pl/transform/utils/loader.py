# pylint: disable=invalid-name, broad-exception-caught, logging-too-many-args
"""Load data"""
import logging
import urllib.parse
from typing import Optional

import pandas as pd
import requests
from settings import Repository
from transform.utils.validate import validate_loaded_pd_df

logger = logging.getLogger(__name__)


def _get_params(per_page: int, start: int, repository: Repository) -> str:
    repo_to_params_map = {
        Repository.REPOD: "?q=*&type=dataset&per_page={per_page}&start={start}",
        Repository.RODBUK: (
            "?q=*&type=dataset&per_page={per_page}&metadata_fields=citation:*"
        ),
    }
    params_string = repo_to_params_map[repository]
    return params_string.format(per_page=per_page, start=start)


def pd_load_datasets_with_pagination(conf: any) -> pd.DataFrame | None:
    """Load datasets from url as pandas df"""
    start = 0
    total = 10000
    per_page = conf.PER_PAGE
    dfs = []
    while start < total:
        try:
            params = _get_params(per_page, start, conf.REPOSITORY)
            url = f"{conf.DATASET_LIST_ADDRESS}{params}"
            response = requests.get(url=url, timeout=conf.TIMEOUT_SECONDS)
            response.raise_for_status()  # Raise an exception for any unsuccessful response
            response_json = response.json()
            data = response_json["data"]["items"]
            count_in_response = response_json["data"]["count_in_response"]
            data = pd.DataFrame(data, index=range(start, start + count_in_response))
            total = response_json["data"]["total_count"]
            validate_loaded_pd_df(response, data)
            dfs.append(data)
        except requests.exceptions.RequestException as e:
            logger.error("Error during the request: %s", e)
        except (KeyError, ValueError) as e:
            logger.error("Error while parsing the response: %s", e)
        except Exception as e:
            logger.error("An unexpected error occurred: %s", e)
        start += per_page
    return pd.concat(dfs) if dfs else None


def fetch_detail_data(doi: str, url: str) -> Optional[dict]:
    """Make a call based on url and doi that will return data lacking on the list endpoint"""
    try:
        encoded_url = f"{url}{urllib.parse.quote(doi)}"  # Encode DOI
        response = requests.get(encoded_url, timeout=conf.TIMEOUT_SECONDS)
        response.raise_for_status()  # Raise an exception for any unsuccessful response
        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        logger.error("Error during the request: %s", e)
        return None
    except (KeyError, ValueError) as e:
        logger.error("Error while parsing the response: %s", e)
        return None
    except Exception as e:
        logger.error("An unexpected error occurred: %s", e)
        return None
