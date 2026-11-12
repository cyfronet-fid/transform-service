import logging
import os
from enum import Enum
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic import AnyUrl
from pydantic_settings import BaseSettings

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
logger = logging.getLogger(__name__)


class Repository(str, Enum):
    REPOD = "repod"
    RODBUK = "rodbuk"


class GlobalSettings(BaseSettings):
    DATASET_LIST_ADDRESS: AnyUrl
    DATASET_DETAIL_ADDRESS: AnyUrl
    SOLR_URL: AnyUrl = "http://149.156.182.2:8983"
    SOLR_EOSCPL_DATASET_COLS_NAME: str = "pl_all_collection pl_dataset"
    PER_PAGE: int = 100
    REPOSITORY: Repository
    TIMEOUT_SECONDS: int = 200
    TOTAL_RECORDS: Optional[int] = None
    DRY_RUN: bool = False
    OUTPUT_DIR: Path = Path(__file__).resolve().parent / "output"


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
    if isinstance(repository, str):
        try:
            repository = Repository(repository.lower())
        except ValueError:
            pass
    settings = CONFIG_MAP.get(repository)
    if not settings:
        logger.error(
            f"Invalid repository name. Allowed values: {[e.value for e in Repository]}."
        )
        raise ValueError(f"Invalid repository name: {repository}")
    return settings()
