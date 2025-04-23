"""Harvest license as str from 'license' - separate calls"""

from pandas import DataFrame
from settings import Repository, get_config
from transform.utils.loader import fetch_detail_data


def get_license(response: dict) -> str:
    """Return license from a response"""
    return response.get("datasetVersion", {}).get("license", {}).get("name")


def harvest_license(df: DataFrame) -> list[str]:
    """Create license column from Rodbuk's 'license' nested field"""
    conf = get_config(Repository.RODBUK)
    license_column = []

    for doi in df["global_id"]:
        license_res = fetch_detail_data(doi, conf.DATASET_DETAIL_ADDRESS)
        license_column.append(get_license(license_res))

    return license_column
