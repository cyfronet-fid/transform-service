# pylint: disable=invalid-name, line-too-long, logging-fstring-interpolation
"""Send data"""

from logging import getLogger

import requests
from requests.exceptions import RequestException

logger = getLogger(__name__)


def send_json_string_to_solr(
    data: str,
    conf: any,
) -> bool:
    """Send data as a json string to solr. Returns True if all collections succeeded."""
    if getattr(conf, "DRY_RUN", False):
        logger.info("DRY_RUN mode active: Skipping sending data to Solr.")
        return True

    success = True
    col_names = conf.SOLR_EOSCPL_DATASET_COLS_NAME.strip().split()
    for col_name in col_names:
        url = f"{conf.SOLR_URL}solr/{col_name}/update?commitWithin=100"
        req_headers = {"Accept": "application/json", "Content-Type": "application/json"}

        try:
            logger.info(f"Sending data to Solr collection: {col_name} at {url}")
            req = requests.post(
                url,
                data=data.encode("utf-8"),
                headers=req_headers,
                timeout=conf.TIMEOUT_SECONDS,
            )
            if req.status_code == 200:
                logger.info(
                    f"Solr update was successful. Collection name={col_name}, status={req.status_code}"
                )
            else:
                success = False
                logger.error(
                    f"Solr update has failed. Collection name={col_name}, status={req.status_code}, body={req.text[:200]}"
                )
        except RequestException as e:
            success = False
            logger.error(
                f"Solr connection failed for collection {col_name} (VPN may be required/disconnected): {e}"
            )

    return success
