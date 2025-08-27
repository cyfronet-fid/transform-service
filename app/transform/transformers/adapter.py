# pylint: disable=line-too-long, wildcard-import, invalid-name, unused-wildcard-import, duplicate-code
"""Transform adapters"""
from datetime import datetime, timezone
from logging import getLogger

from dateutil import parser
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import array, col, lit, split, when
from pyspark.sql.types import (
    DateType,
    StructField,
    StructType,
)

from app.settings import settings
from app.transform.transformers.base.base import BaseTransformer
from app.transform.utils.common import (
    transform_date,
)
from app.transform.utils.utils import sort_schema
from schemas.old.output.adapter import adapter_output_schema
from schemas.properties.data import *

logger = getLogger(__name__)


class AdapterTransformer(BaseTransformer):
    """Transformer used to transform adapters"""

    def __init__(self, spark: SparkSession):
        self.type = settings.ADAPTER
        self.exp_output_schema = adapter_output_schema

        super().__init__(
            self.type,
            self.cols_to_add,
            self.cols_to_drop,
            self.cols_to_rename,
            self.exp_output_schema,
            spark,
        )

    def apply_simple_trans(self, df: DataFrame) -> DataFrame:
        """Apply simple transformations.
        Simple in a way that there is a possibility to manipulate the main dataframe
        without a need to create another dataframe and merging"""
        df = df.withColumn(TYPE, lit(self.type))
        df = self.rename_cols(df)

        return df

    def apply_complex_trans(self, df: DataFrame) -> DataFrame:
        """Harvest oag properties that requires more complex transformations
        Basically from those harvested properties there will be created another dataframe
        which will be later on merged with the main dataframe"""
        df = self.standardize_publication_date(df)
        df = self.extract_linked_resources_native(df)

        return df

    def cast_columns(self, df: DataFrame) -> DataFrame:
        """Cast trainings columns"""
        df = df.withColumn("catalogues", split(col("catalogues"), ","))
        df = df.withColumn("changelog", split(col("changelog"), ","))
        df = transform_date(df, "publication_date", "yyyy-MM-dd")

        return df

    @property
    def harvested_schema(self):
        """Schema of harvested properties"""
        return sort_schema(
            StructType(
                [
                    StructField(PUBLICATION_DATE, DateType(), True),
                ]
            )
        )

    @property
    def cols_to_add(self) -> None:
        """Add those columns to the dataframe"""
        return None

    @property
    def cols_to_drop(self) -> tuple:
        """Drop those columns from the dataframe"""
        return ("admins",)

    @property
    def cols_to_rename(self) -> dict[str, str]:
        """Columns to rename. Keys are mapped to the values"""
        return {
            "catalogueId": "catalogues",
            "changeLog": "changelog",
            "documentation": "documentation_url",
            "name": "title",
            "lastUpdate": "publication_date",
            "programmingLanguage": "programming_language",
            "tagline": "keywords",
        }

    def standardize_publication_date(self, df: DataFrame) -> DataFrame:
        """Convert ISO datetime strings with offsets or Unix timestamps to
        UTC-aware datetime objects (for Spark TimestampType)."""
        pub_date_raw = df.select(PUBLICATION_DATE).collect()

        pub_date_column = []
        for row in pub_date_raw:
            pub_date_value = row[PUBLICATION_DATE]

            if isinstance(pub_date_value, str):
                # Handle ISO datetime string
                parsed_date = (
                    parser.isoparse(pub_date_value)
                    .astimezone(timezone.utc)
                    .replace(microsecond=0)
                )
            elif isinstance(pub_date_value, (int, float)):
                # Handle Unix timestamp in milliseconds
                timestamp_seconds = pub_date_value / 1000
                parsed_date = datetime.fromtimestamp(
                    timestamp_seconds, tz=timezone.utc
                ).replace(microsecond=0)
            else:
                raise ValueError(
                    f"Unexpected publication date format: {type(pub_date_value)} - {pub_date_value}"
                )

            pub_date_column.append(parsed_date)

        self.harvested_properties[PUBLICATION_DATE] = pub_date_column

        return df.drop(PUBLICATION_DATE)

    @staticmethod
    def extract_linked_resources_native(df: DataFrame) -> DataFrame:
        """Extract related guidelines and services using PySpark operations only"""
        if "linkedResource" not in df.columns:
            logger.warning("linkedResource column not found in DataFrame")
            return df.withColumn("related_guidelines", array()).withColumn(
                "related_services", array()
            )

        try:
            # Add related_guidelines and related_services columns based on linkedResource
            df = df.withColumn(
                "related_guidelines",
                when(
                    (col("linkedResource").isNotNull())
                    & (col("linkedResource.type") == "Guideline")
                    & (col("linkedResource.id").isNotNull()),
                    array(col("linkedResource.id")),
                ).otherwise(array()),
            ).withColumn(
                "related_services",
                when(
                    (col("linkedResource").isNotNull())
                    & (col("linkedResource.type") == "Service")
                    & (col("linkedResource.id").isNotNull()),
                    array(col("linkedResource.id")),
                ).otherwise(array()),
            )

            # Drop the original linkedResource column
            return df.drop("linkedResource")

        except Exception as e:
            logger.error(f"Error processing linkedResource with native approach: {e}")
            # Fallback: add empty arrays and keep original column if it exists
            return df.withColumn("related_guidelines", array()).withColumn(
                "related_services", array()
            )
