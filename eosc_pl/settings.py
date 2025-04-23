import logging
import os
from enum import Enum

from dotenv import load_dotenv
from pydantic import AnyUrl
from pydantic_settings import BaseSettings

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
logger = logging.getLogger(__name__)


class Repository(Enum):
    REPOD = "repod"
    RODBUK = "rodbuk"


class GlobalSettings(BaseSettings):
    DATASET_LIST_ADDRESS: AnyUrl
    DATASET_DETAIL_ADDRESS: AnyUrl
    SOLR_URL: AnyUrl = "http://149.156.182.2:8983"
    SOLR_EOSCPL_DATASET_COLS_NAME: str = "pl_all_collection pl_dataset"
    PER_PAGE: int = 1000
    REPOSITORY: Repository
    TIMEOUT_SECONDS: 200


class RepodSettings(GlobalSettings):
    DATASET_LIST_ADDRESS: AnyUrl = "https://repod.icm.edu.pl/api/search"
    DATASET_DETAIL_ADDRESS: AnyUrl = (
        "https://repod.icm.edu.pl/api/datasets/export?exporter=dataverse_json&persistentId=doi:"
    )
    REPOSITORY: Repository = Repository.REPOD


class RodbukSettings(GlobalSettings):
    DATASET_LIST_ADDRESS: AnyUrl = "https://rodbuk.pl/api/search"
    DATASET_DETAIL_ADDRESS: AnyUrl = (
        "https://rodbuk.pl/api/datasets/export?exporter=dataverse_json&persistentId="
    )
    REPOSITORY: Repository = Repository.RODBUK


CONFIG_MAP = {
    Repository.REPOD: RepodSettings,
    Repository.RODBUK: RodbukSettings,
}


def get_config(repository):
    settings = CONFIG_MAP.get(repository)
    if not settings:
        logger.error(
            f"Invalid repository name. Allowed values: {[e.value for e in Repository]}."
        )
        raise ValueError(f"Invalid repository name: {repository}")
    return settings()
