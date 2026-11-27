# pylint: disable=line-too-long, wildcard-import, unused-wildcard-import, invalid-name, duplicate-code
"""Transform Deployable Services"""

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import col, concat, expr, lit, split
from pyspark.sql.types import StringType, StructType

from app.settings import settings
from app.transform.transformers.base.base import BaseTransformer
from app.transform.utils.utils import sort_schema
from schemas.old.output.deployable_service import deployable_service_output_schema
from schemas.properties.data import ID, TYPE


class DeployableServiceTransformer(BaseTransformer):
    """Transformer used to transform deployable services"""

    def __init__(self, spark: SparkSession):
        self.type = settings.DEPLOYABLE_SERVICE
        self.id_increment = settings.DEPLOYABLE_SERVICE_IDS_INCREMENTOR
        self.exp_output_schema = deployable_service_output_schema

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
        df = df.withColumn(ID, (col(ID) + self.id_increment))
        df = self.transform_creators(df)

        return df

    def apply_complex_trans(self, df: DataFrame) -> DataFrame:
        """Harvest properties that requires more complex transformations
        Basically from those harvested properties there will be created another dataframe
        which will be later on merged with the main dataframe"""

        return df

    @property
    def harvested_schema(self) -> StructType:
        """Schema of harvested properties"""
        return sort_schema(StructType([]))

    @staticmethod
    def cast_columns(df: DataFrame) -> DataFrame:
        """Cast certain columns"""
        df = (
            df.withColumn("publication_date", col("publication_date").cast("date"))
            .withColumn("updated_at", col("updated_at").cast("date"))
            .withColumn("last_update", col("last_update").cast("date"))
            .withColumn("synchronized_at", col("synchronized_at").cast("date"))
            .withColumn("id", col("id").cast(StringType()))
            .withColumn("catalogues", split(col("catalogues"), ","))
        )

        return df

    @property
    def cols_to_rename(self) -> dict[str, str]:
        """Columns to rename. Keys are mapped to the values"""
        return {
            "name": "title",
            "tag_list": "keywords",
            "license_name": "license",
            "catalogue": "catalogues",
            "public_contact_emails": "public_contacts",
        }

    @property
    def cols_to_add(self) -> None:
        """Add those columns to the dataframe"""
        return None

    @property
    def cols_to_drop(self) -> tuple[str, ...]:
        """Drop those columns from the dataframe"""
        return (
            "resource_type",
            "publishing_date",  # TODO MP AI hallucination?
            "urls",  # TODO MP AI hallucination?
        )

    @staticmethod
    def transform_creators(df: DataFrame) -> DataFrame:
        """
        Transform creator metadata into fields used for Solr indexing.

        The current deployable service schema provides only the creator's
        first name, last name and email address. These values are used to
        create searchable creator-related fields for Solr.

        The following fields are created:

        - creator_names:
            Creator full names built from first and last names.
        - creator_identifiers:
            Creator email addresses.
        - creators_searchable:
            Searchable text combining creator names and email addresses.
        """

        creators = "coalesce(creators, array())"

        # Extract creator names.
        df = df.withColumn(
            "creator_names",
            expr(f"""
                transform({creators}, x ->
                    nullif(trim(concat_ws(' ', x.firstName, x.lastName)), '')
                )
            """),
        )

        # Extract creator identifiers (currently email addresses).
        df = df.withColumn(
            "creator_identifiers",
            expr(f"""
                transform({creators}, x ->
                    nullif(x.email, '')
                )
            """),
        )

        # Build searchable creator text.
        df = df.withColumn(
            "creators_searchable",
            expr(f"""
                transform({creators}, x ->
                    trim(concat_ws(
                        ' ',
                        nullif(trim(concat_ws(' ', x.firstName, x.lastName)), ''),
                        nullif(x.email, '')
                    ))
                )
            """),
        )

        return df
