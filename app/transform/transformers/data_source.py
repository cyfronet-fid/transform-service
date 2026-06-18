# pylint: disable=duplicate-code
"""Transform data sources"""

from pyspark.sql.types import (
    ArrayType,
    BooleanType,
    IntegerType,
    StringType,
    StructField,
    StructType,
)

from app.settings import logger, settings
from app.transform.transformers.base.marketplace import MarketplaceBaseTransformer
from app.transform.utils.utils import sort_schema
from schemas.properties.data import (
    BEST_ACCESS_RIGHT,
    OPEN_ACCESS,
    POPULARITY,
)
from schemas.se.data_source import DataSourceSESchema


class DataSourceTransformer(MarketplaceBaseTransformer):
    """Data source transformer"""

    def __init__(self, spark):
        self.type = settings.DATASOURCE
        id_increment = settings.DATA_SOURCE_IDS_INCREMENTOR
        self.exp_output_schema = DataSourceSESchema

        super().__init__(
            id_increment,
            self.type,
            self.cols_to_add,
            self.cols_to_drop,
            self.exp_output_schema,
            spark,
        )

        logger.error("yoo 3")

    @property
    def harvested_schema(self) -> StructType:
        """Schema of harvested properties"""
        return sort_schema(
            StructType(
                [
                    StructField(BEST_ACCESS_RIGHT, StringType(), True),
                    StructField(OPEN_ACCESS, BooleanType(), True),
                    StructField(POPULARITY, IntegerType(), True),
                ]
            )
        )

    @property
    def cols_to_add(self) -> None:
        """Add those columns to the dataframe"""
        return None

    @property
    def cols_to_drop(self) -> None:
        """Drop those columns from the dataframe"""
        return None

    @property
    def cols_to_rename(self) -> dict[str, str]:
        """Columns to rename. Keys are mapped to the values"""
        return {
            "order_type": "best_access_right",
            "name": "title",
            "public_contact_emails": "public_contacts",
            "trls": "trl",
            "urls": "url",
        }
