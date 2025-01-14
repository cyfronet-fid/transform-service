# pylint: disable=too-few-public-methods
"""Configs for all the environments"""
import logging
import os
from typing import Literal, Optional

from dotenv import load_dotenv
from pydantic import AnyUrl
from pydantic_settings import BaseSettings, SettingsConfigDict

from schemas.old.input import *
from schemas.old.output import *

logger = logging.getLogger(__name__)
EnvironmentType = Literal["dev", "test", "production"]
load_dotenv(os.path.join(os.path.dirname(__file__), "../.env"))


class GlobalSettings(BaseSettings):
    """Common configuration parameters shared between all environments"""

    # General
    ENVIRONMENT: EnvironmentType = "dev"
    LOG_LEVEL: str = logging.getLevelName(logging.INFO)
    TESTING: bool = False
    RELATIONS: dict = {}  # Set in TransformSettings
    COLLECTIONS: dict = {}  # Set in TransformSettings
    SENTRY_DSN: Optional[str] = None

    # Services
    # - Solr
    SOLR_URL: AnyUrl = "http://localhost:8983"
    SOLR_COLS_PREFIX: str = ""
    #   - Default Solr collections configurations
    # See: https://github.com/cyfronet-fid/eosc-search-service/blob/7e73eb17ec730b73ac54e002608e391e58b1d1e8/transform/docs/configs.md
    SOLR_ALL_COL_CONF: str = "all_collection_oag56_v205"  # All collection
    SOLR_ORG_CONF: str = "organisation_v106"  # Organisation
    SOLR_PROJ_CONF: str = "project_v102"  # Project
    SOLR_PROVIDER_CONF: str = "provider_v101"  # Provider
    SOLR_CAT_CONF: str = "catalogue_v101"  # Catalogue

    # - S3
    S3_ACCESS_KEY: str = ""
    S3_SECRET_KEY: str = ""
    S3_ENDPOINT: AnyUrl = "https://example.com"
    S3_BUCKET: str = ""

    # - STOMP
    STOMP_SUBSCRIPTION: bool = True
    STOMP_HOST: str = "127.0.0.1"
    STOMP_PORT: int = 61613
    STOMP_LOGIN: str = "guest"
    STOMP_PASS: str = "guest"
    STOMP_TOPICS: list[str] = [
        "/topic/training_resource.update",
        "/topic/training_resource.create",
        "/topic/training_resource.delete",
        "/topic/interoperability_record.update",
        "/topic/interoperability_record.create",
        "/topic/interoperability_record.delete",
    ]
    STOMP_CLIENT_NAME: str = "transformer-client"
    STOMP_SSL: bool = False

    # Sources of data
    # - Local storage with OAG data
    DATASET_PATH: str = "input/dataset"
    PUBLICATION_PATH: str = "input/publication"
    SOFTWARE_PATH: str = "input/software"
    OTHER_RP_PATH: str = "input/other_rp"
    ORGANISATION_PATH: str = "input/organization"
    PROJECT_PATH: str = "input/project"

    # - Relations
    RES_ORG_REL_PATH: str = "input/resultOrganization"
    RES_PROJ_REL_PATH: str = "input/resultProject"
    ORG_PROJ_REL_PATH: str = "input/organizationProject"

    # - Marketplace
    MP_API_ADDRESS: AnyUrl = "https://marketplace.sandbox.eosc-beyond.eu"
    MP_API_TOKEN: str = ""

    # - Provider Component
    GUIDELINE_ADDRESS: AnyUrl = (
        "https://integration.providers.sandbox.eosc-beyond.eu/api/public/interoperabilityRecord/all?catalogue_id=all&active=true&suspended=false&quantity=10000"
    )
    TRAINING_ADDRESS: AnyUrl = (
        "https://integration.providers.sandbox.eosc-beyond.eu/api/public/trainingResource/all?catalogue_id=all&active=true&suspended=false&quantity=10000"
    )

    # Transformation General Settings TODO
    # INPUT_FORMAT: str = "json"
    # OUTPUT_FORMAT: str = "json"

    # Defined data types, "type" property of each data type
    SOFTWARE: str = "software"
    OTHER_RP: str = "other"
    DATASET: str = "dataset"
    PUBLICATION: str = "publication"
    ORGANISATION: str = "organisation"
    PROJECT: str = "project"
    SERVICE: str = "service"
    DATASOURCE: str = "data source"
    PROVIDER: str = "provider"
    OFFER: str = "offer"
    BUNDLE: str = "bundle"
    GUIDELINE: str = "interoperability guideline"
    TRAINING: str = "training"
    CATALOGUE: str = "catalogue"
    RESULT_ORGANISATION: str = "resultOrganisation"
    RESULT_PROJECT: str = "resultProject"
    ORGANISATION_PROJECT: str = "organisationProject"

    # Relations properties
    TMP_DIRECTORY: str = "tmp/"
    DIRECTORIES_WITH_ADDITIONAL_COLUMNS: str = "DIRECTORIES_WITH_ADDITIONAL_COLUMNS"
    SINGLE_DIRECTORIES: str = "SINGLE_DIRECTORIES"
    DATA_DIRECTORIES: str = "DATA_DIRECTORIES"
    RESULT_RELATION_DIRECTORIES: str = "RESULT_RELATION_DIRECTORIES"
    ORGANISATION_PROJECT_RELATION_DIRECTORIES: str = (
        "ORGANISATION_PROJECT_RELATION_DIRECTORIES"
    )

    # Raw solr collection names
    SOLR_COLLECTION_NAMES: list[str] = [
        "all_collection",
        "software",
        "other_rp",
        "dataset",
        "publication",
        "organisation",
        "project",
        "service",
        "data_source",
        "provider",
        "offer",
        "bundle",
        "guideline",
        "training",
        "catalogue",
    ]

    # IDs incrementors
    SERVICE_IDS_INCREMENTOR: int = 0  # No change
    OFFER_IDS_INCREMENTOR: int = 10_000
    PROVIDER_IDS_INCREMENTOR: int = 100_000
    BUNDLE_IDS_INCREMENTOR: int = 1_000_000
    DATA_SOURCE_IDS_INCREMENTOR: int = 10_000_000
    CATALOGUE_IDS_INCREMENTOR: int = 100_000_000

    # EOSC PL
    DATASET_ADDRESS: str = (
        "https://rodbuk.pl/api/search?q=*&type=dataset&per_page=1000&metadata_fields=citation:*"
    )
    LICENSE_ADDRESS: str = (
        "https://rodbuk.pl/api/datasets/export?exporter=dataverse_json&persistentId="
    )
    SOLR_EOSCPL_DATASET_COLS_NAME: str = "pl_all_collection pl_dataset"

    # Get config from .env
    model_config = SettingsConfigDict(
        env_file="../../../../transform-service/.env", env_file_encoding="utf-8"
    )


class TransformSettings(GlobalSettings):
    """Transformation configuration"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.RELATIONS = self.get_relations_config()
        self.COLLECTIONS = self.get_collections_config()

    def get_relations_config(self) -> dict:
        """Get relations config"""

        relations = {
            self.DIRECTORIES_WITH_ADDITIONAL_COLUMNS: (self.ORGANISATION_PATH,),
            self.SINGLE_DIRECTORIES: (
                self.ORGANISATION_PATH,
                self.PROJECT_PATH,
            ),
            self.DATA_DIRECTORIES: (
                self.ORGANISATION_PATH,
                self.PROJECT_PATH,
                self.PUBLICATION_PATH,
                self.DATASET_PATH,
                self.SOFTWARE_PATH,
                self.OTHER_RP_PATH,
            ),
            self.RESULT_RELATION_DIRECTORIES: (
                self.RES_ORG_REL_PATH,
                self.RES_PROJ_REL_PATH,
            ),
            self.ORGANISATION_PROJECT_RELATION_DIRECTORIES: (self.ORG_PROJ_REL_PATH,),
        }

        return relations

    def get_collections_config(self) -> dict:
        """Get collections config"""
        OUTPUT_SCHEMA = "OUTPUT_SCHEMA"
        INPUT_SCHEMA = "INPUT_SCHEMA"
        PATH = "PATH"
        ADDRESS = "ADDRESS"

        mp_api = str(self.MP_API_ADDRESS) + "/api/v1/ess/"

        collections = {
            self.SOFTWARE: {
                PATH: self.SOFTWARE_PATH,
                OUTPUT_SCHEMA: software_output_schema,
                INPUT_SCHEMA: software_input_schema,
            },
            self.OTHER_RP: {
                PATH: self.OTHER_RP_PATH,
                OUTPUT_SCHEMA: other_rp_output_schema,
                INPUT_SCHEMA: other_rp_input_schema,
            },
            self.DATASET: {
                PATH: self.DATASET_PATH,
                OUTPUT_SCHEMA: dataset_output_schema,
                INPUT_SCHEMA: dataset_input_schema,
            },
            self.PUBLICATION: {
                PATH: self.PUBLICATION_PATH,
                OUTPUT_SCHEMA: publication_output_schema,
                INPUT_SCHEMA: publication_input_schema,
            },
            self.ORGANISATION: {
                PATH: self.ORGANISATION_PATH,
                OUTPUT_SCHEMA: organisation_output_schema,
                INPUT_SCHEMA: organisation_input_schema,
            },
            self.PROJECT: {
                PATH: self.PROJECT_PATH,
                OUTPUT_SCHEMA: project_output_schema,
                INPUT_SCHEMA: project_input_schema,
            },
            self.SERVICE: {
                ADDRESS: mp_api + "services",
                OUTPUT_SCHEMA: service_output_schema,
                INPUT_SCHEMA: service_input_schema,
            },
            self.DATASOURCE: {
                ADDRESS: mp_api + "datasources",
                OUTPUT_SCHEMA: data_source_output_schema,
                INPUT_SCHEMA: data_source_input_schema,
            },
            self.BUNDLE: {
                ADDRESS: mp_api + "bundles",
                OUTPUT_SCHEMA: bundle_output_schema,
                INPUT_SCHEMA: bundle_input_schema,
            },
            self.GUIDELINE: {
                ADDRESS: str(self.GUIDELINE_ADDRESS),
                OUTPUT_SCHEMA: guideline_output_schema,
                INPUT_SCHEMA: guideline_input_schema,
            },
            self.TRAINING: {
                ADDRESS: str(self.TRAINING_ADDRESS),
                OUTPUT_SCHEMA: training_output_schema,
                INPUT_SCHEMA: training_input_schema,
            },
            self.PROVIDER: {
                ADDRESS: mp_api + "providers",
                OUTPUT_SCHEMA: provider_output_schema,
                INPUT_SCHEMA: provider_input_schema,
            },
            self.OFFER: {
                ADDRESS: mp_api + "offers",
                OUTPUT_SCHEMA: offer_output_schema,
                INPUT_SCHEMA: offer_input_schema,
            },
            self.CATALOGUE: {
                ADDRESS: mp_api + "catalogues",
                OUTPUT_SCHEMA: catalogue_output_schema,
                INPUT_SCHEMA: catalogue_input_schema,
            },
        }

        return self.get_solr_col_names(collections)

    def get_solr_col_names(self, collections: dict) -> dict:
        """Get solr collections names of each data type.
        To those collections, data of that specific type will be sent"""
        prefix = self.SOLR_COLS_PREFIX
        solr_col_names = {
            self.SOFTWARE: (prefix + "all_collection", prefix + "software"),
            self.OTHER_RP: (prefix + "all_collection", prefix + "other_rp"),
            self.DATASET: (prefix + "all_collection", prefix + "dataset"),
            self.PUBLICATION: (prefix + "all_collection", prefix + "publication"),
            self.ORGANISATION: (
                prefix + "organisation",
            ),  # Commas create tuples here for easy iteration later on
            self.PROJECT: (prefix + "project",),
            self.SERVICE: (prefix + "all_collection", prefix + "service"),
            self.DATASOURCE: (
                prefix + "all_collection",
                prefix + "service",
                prefix + "data_source",
            ),
            self.BUNDLE: (prefix + "all_collection", prefix + "bundle"),
            self.GUIDELINE: (prefix + "all_collection", prefix + "guideline"),
            self.TRAINING: (prefix + "all_collection", prefix + "training"),
            self.PROVIDER: (prefix + "provider",),
            self.OFFER: (prefix + "offer",),
            self.CATALOGUE: (prefix + "catalogue",),
        }

        return {
            col_name: {**val, "SOLR_COL_NAMES": solr_col_names[col_name]}
            for col_name, val in collections.items()
        }


class ProductionSettings(TransformSettings):
    SOLR_URL: AnyUrl = "http://149.156.182.69:8983"
    GUIDELINE_ADDRESS: AnyUrl = (
        "https://providers.eosc-portal.eu/api/public/interoperabilityRecord/all?catalogue_id=all&active=true&suspended=false&quantity=10000"
    )
    TRAINING_ADDRESS: AnyUrl = (
        "https://providers.eosc-portal.eu/api/public/trainingResource/all?catalogue_id=all&active=true&suspended=false&quantity=10000"
    )


class DevSettings(TransformSettings):
    SOLR_URL: AnyUrl = "http://149.156.182.2:8983"
    STOMP_SUBSCRIPTION: bool = False


class TestSettings(TransformSettings):
    TESTING: bool = True
    SOLR_URL: AnyUrl = "http://localhost:8983"
    SOLR_COLS_PREFIX: str = "test_"

    # STOMP Settings for Testing
    STOMP_SUBSCRIPTION: bool = True
    STOMP_HOST: str = "localhost"
    STOMP_PORT: int = 61613
    STOMP_LOGIN: str = "test_user"
    STOMP_PASS: str = "test_pass"
    STOMP_TOPICS: list[str] = [
        "/topic/test_resource.update",
        "/topic/test_resource.create",
        "/topic/test_resource.delete",
    ]
    STOMP_CLIENT_NAME: str = "test-transformer-client"
    STOMP_SSL: bool = False


class Settings(GlobalSettings):
    def get_settings(self) -> GlobalSettings:
        _settings = {
            "dev": DevSettings,
            "test": TestSettings,
            "production": ProductionSettings,
        }
        return _settings[self.ENVIRONMENT]()


settings = Settings().get_settings()
