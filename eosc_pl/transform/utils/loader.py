# pylint: disable=invalid-name, broad-exception-caught, logging-too-many-args
"""Load data"""

import json
import logging
import urllib.parse
from pathlib import Path
from typing import Optional

import pandas as pd
import requests

from eosc_pl.settings import Repository
from eosc_pl.transform.utils.validate import validate_loaded_pd_df

logger = logging.getLogger(__name__)


def _get_params(per_page: int, start: int, repository: Repository) -> str:
    repo_to_params_map = {
        Repository.REPOD: "?q=*&type=dataset&per_page={per_page}&start={start}",
        Repository.RODBUK: (
            "?q=*&type=dataset&per_page={per_page}&start={start}&metadata_fields=citation:*"
        ),
    }
    params_string = repo_to_params_map[repository]
    return params_string.format(per_page=per_page, start=start)


def load_datasets_from_file(
    file_path: str | Path, max_records: Optional[int] = None
) -> pd.DataFrame | None:
    """Load datasets from local JSON/txt file (e.g. repod.txt or rodbuk.txt)"""
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"File not found: {file_path}")

    logger.info("Loading datasets from file: %s", path)
    with open(path, "r", encoding="utf-8") as f:
        content = json.load(f)

    if isinstance(content, dict):
        if (
            "data" in content
            and isinstance(content["data"], dict)
            and "items" in content["data"]
        ):
            items = content["data"]["items"]
        elif "items" in content:
            items = content["items"]
        else:
            items = [content]
    elif isinstance(content, list):
        items = content
    else:
        raise ValueError(f"Unexpected JSON structure in {file_path}")

    if max_records is not None and max_records > 0:
        items = items[:max_records]

    logger.info("Loaded %d records from file %s", len(items), path.name)
    return pd.DataFrame(items)


def pd_load_datasets_with_pagination(
    conf: any, max_records: Optional[int] = None
) -> pd.DataFrame | None:
    """Load datasets from url as pandas df"""
    start = 0
    total = max_records if max_records is not None else 10000
    per_page = conf.PER_PAGE
    dfs = []
    while start < total:
        try:
            current_per_page = (
                min(per_page, total - start) if max_records is not None else per_page
            )
            params = _get_params(current_per_page, start, conf.REPOSITORY)
            url = f"{conf.DATASET_LIST_ADDRESS}{params}"
            logger.info("Fetching: %s", url)
            response = requests.get(url=url, timeout=conf.TIMEOUT_SECONDS)
            response.raise_for_status()  # Raise an exception for any unsuccessful response
            response_json = response.json()
            data = response_json["data"]["items"]
            count_in_response = response_json["data"]["count_in_response"]
            if count_in_response == 0:
                break
            data = pd.DataFrame(data, index=range(start, start + count_in_response))
            api_total = response_json["data"]["total_count"]
            if max_records is not None:
                total = min(api_total, max_records)
            else:
                total = api_total
            validate_loaded_pd_df(response, data)
            dfs.append(data)
        except requests.exceptions.RequestException as e:
            logger.error("Error during the request: %s", e)
            break
        except (KeyError, ValueError) as e:
            logger.error("Error while parsing the response: %s", e)
            break
        except Exception as e:
            logger.error("An unexpected error occurred: %s", e)
            break
        start += per_page
    return pd.concat(dfs, ignore_index=True) if dfs else None


def fetch_detail_data(
    doi: str,
    url: str,
    timeout: int = 200,
    session: Optional[requests.Session] = None,
) -> Optional[dict]:
    """Make a call based on url and doi that will return data lacking on the list endpoint"""
    try:
        encoded_url = f"{url}{urllib.parse.quote(doi)}"  # Encode DOI
        client = session if session is not None else requests
        response = client.get(encoded_url, timeout=timeout)
        response.raise_for_status()  # Raise an exception for any unsuccessful response
        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        logger.error("Error during detail request for %s: %s", doi, e)
        return None
    except (KeyError, ValueError) as e:
        logger.error("Error while parsing detail response for %s: %s", doi, e)
        return None
    except Exception as e:
        logger.error("An unexpected error occurred for detail %s: %s", doi, e)
        return None


def fetch_details_concurrently(
    dois: list[str],
    url: str,
    timeout: int = 200,
    max_workers: int = 16,
) -> list[Optional[dict]]:
    """Fetch detail records concurrently using a persistent session and ThreadPoolExecutor.

    Maintains exact order of input DOIs.
    """
    if not dois:
        return []

    import concurrent.futures

    from requests.adapters import HTTPAdapter

    session = requests.Session()
    adapter = HTTPAdapter(
        pool_connections=max_workers,
        pool_maxsize=max_workers,
        max_retries=2,
    )
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    def _fetch_one(doi: str) -> Optional[dict]:
        if not doi:
            return None
        return fetch_detail_data(doi, url, timeout=timeout, session=session)

    effective_workers = min(max_workers, max(1, len(dois)))
    with concurrent.futures.ThreadPoolExecutor(
        max_workers=effective_workers
    ) as executor:
        results = list(executor.map(_fetch_one, dois))

    return results
