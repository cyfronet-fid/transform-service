"""Harvest license as str from 'license' - separate calls"""

from pandas import DataFrame

from eosc_pl.settings import Repository, get_config
from eosc_pl.transform.utils.loader import fetch_detail_data, fetch_details_concurrently


def get_license(response: dict | None) -> str | None:
    """Return license from a response"""
    if not response or not isinstance(response, dict):
        return None
    return response.get("datasetVersion", {}).get("license", {}).get("name")


def harvest_license(df: DataFrame) -> list[str | None]:
    """Create license column from Rodbuk's 'license' nested field using concurrent fetching"""
    if "global_id" not in df.columns:
        return [None] * len(df)

    conf = get_config(Repository.RODBUK)
    dois = list(df["global_id"])

    detail_results = fetch_details_concurrently(
        dois,
        conf.DATASET_DETAIL_ADDRESS,
        timeout=conf.TIMEOUT_SECONDS,
        max_workers=16,
    )

    return [get_license(res) for res in detail_results]
