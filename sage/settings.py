from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Pydantic v2 config
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
    )

    # Aggregator API
    aggregator_url: AnyHttpUrl = Field(..., alias="AGGREGATOR_URL")
    aggregator_api_key: str = Field(..., alias="AGGREGATOR_API_KEY")
    aggregator_api_limit: int = Field(20, alias="AGGREGATOR_API_LIMIT")

    # Solr target
    solr_url: AnyHttpUrl = Field(..., alias="SOLR_URL")
    solr_cols_name: str = Field(..., alias="SOLR_COLS_NAME")

    # Network
    request_timeout: int = Field(30, alias="REQUEST_TIMEOUT")


settings = Settings()
