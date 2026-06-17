# pylint: disable=duplicate-code
"""Transform services"""

from pyspark.sql import DataFrame
from pyspark.sql.functions import array, col, lit
from pyspark.sql.types import (
    BooleanType,
    IntegerType,
    StringType,
    StructField,
    StructType,
)

from app.settings import settings
from app.transform.transformers.base.marketplace import MarketplaceBaseTransformer
from app.transform.utils.utils import sort_schema
from schemas.properties.data import BEST_ACCESS_RIGHT, OPEN_ACCESS, POPULARITY
from schemas.se.service import ServiceSESchema


class ServiceTransformer(MarketplaceBaseTransformer):
    """Service transformer"""

    def __init__(self, spark):
        self.type = settings.SERVICE
        id_increment = settings.SERVICE_IDS_INCREMENTOR
        self.exp_output_schema = ServiceSESchema

        super().__init__(
            id_increment,
            self.type,
            self.cols_to_add,
            self.cols_to_drop,
            self.exp_output_schema,
            spark,
        )

    def apply_simple_trans(self, df: DataFrame) -> DataFrame:
        """Apply simple transformations.
        Simple in a way that there is a possibility to manipulate the main dataframe
        without a need to create another dataframe and merging"""
        df = super().apply_simple_trans(df)

        df = df.withColumn("catalogues", array(lit("eosc")))
        df = df.withColumn("catalogue", col("catalogues")[0])

        return df

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
    def cols_to_drop(self) -> tuple[str, ...]:
        """Drop those columns from the dataframe"""
        return ("public_contacts",)

    @property
    def cols_to_rename(self) -> dict[str, str]:
        """Columns to rename. Keys are mapped to the values"""
        return {
            "nodes": "node",
            "name": "title",
            "order_type": "best_access_right",
            "urls": "url",
            "trls": "trl",
        }

    @staticmethod
    def cast_columns(df: DataFrame) -> DataFrame:
        """Cast certain columns"""
        df = (
            df.withColumn("id", col("id").cast(StringType()))
            .withColumn("updated_at", col("updated_at").cast("date"))
            .withColumn("publication_date", col("publication_date").cast("date"))
            .withColumn("synchronized_at", col("synchronized_at").cast("date"))
        )

        return df
