# pylint: disable=line-too-long, wildcard-import, invalid-name, unused-wildcard-import, duplicate-code
"""Transform adapters"""

from datetime import datetime, timezone
from logging import getLogger

from dateutil import parser
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import (
    array,
    col,
    initcap,
    lit,
    regexp_replace,
    split,
    trim,
    udf,
    when,
)
from pyspark.sql.types import (
    ArrayType,
    DateType,
    StringType,
    StructField,
    StructType,
)

from app.settings import settings
from app.transform.transformers.base.base import BaseTransformer
from app.transform.utils.common import (
    transform_date,
)
from app.transform.utils.utils import sort_schema
from schemas.properties.data import *
from schemas.se.adapter import AdapterSESchema

logger = getLogger(__name__)


class AdapterTransformer(BaseTransformer):
    """Transformer used to transform adapters"""

    def __init__(self, spark: SparkSession):
        self.type = settings.ADAPTER
        self.exp_output_schema = AdapterSESchema

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
        df = self.rename_cols(df)
        df = df.withColumn("catalogues", array(lit("eosc")))
        df = df.withColumn(TYPE, lit(self.type))

        return df

    def apply_complex_trans(self, df: DataFrame) -> DataFrame:
        """Harvest oag properties that requires more complex transformations
        Basically from those harvested properties there will be created another dataframe
        which will be later on merged with the main dataframe"""
        df = self.clean_description(df)
        df = self.standardize_publication_date(df)
        df = self.extract_linked_resources_native(df)
        df = self.extract_sqa(df)
        df = self.extract_license(df)
        df = self.extract_urls(df)
        df = self.extract_alternative_ids(df)
        df = self.extract_creators(df)

        return df

    def cast_columns(self, df: DataFrame) -> DataFrame:
        """Cast trainings columns"""
        df = df.withColumn("changelog", split(col("changelog"), ","))
        df = transform_date(df, "publication_date", "yyyy-MM-dd")
        df = transform_date(df, "last_update", "yyyy-MM-dd")

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
            "changeLog": "changelog",
            "documentation": "documentation_url",
            "name": "title",
            "nodePID": "node",
            "publishingDate": "publication_date",
            "lastUpdate": "last_update",
            "programmingLanguage": "programming_language",
            "publicContacts": "public_contacts",
            "resourceOwner": "resource_owner",
            "tagline": "keywords",
            "urls": "url",
        }

    def standardize_publication_date(self, df: DataFrame) -> DataFrame:
        """Convert ISO datetime strings with offsets or Unix timestamps to
        UTC-aware datetime objects (for Spark TimestampType)."""
        pub_date_raw = df.select(PUBLICATION_DATE).collect()

        pub_date_column = []
        for row in pub_date_raw:
            pub_date_value = row[PUBLICATION_DATE]

            if isinstance(pub_date_value, str):
                if len(pub_date_value) == 10:
                    parsed_date = datetime.fromisoformat(pub_date_value).replace(
                        tzinfo=timezone.utc
                    )
                else:
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
                    & (
                        col("linkedResource.resource_type").isin(
                            "Guideline",
                            "guideline",
                            "interoperability_record",
                            "interoperability_guideline",
                        )
                    )
                    & (col("linkedResource.id").isNotNull()),
                    array(col("linkedResource.id")),
                ).otherwise(array()),
            ).withColumn(
                "related_services",
                when(
                    (col("linkedResource").isNotNull())
                    & (
                        col("linkedResource.resource_type").isin(
                            "Service",
                            "service",
                        )
                    )
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

    @staticmethod
    def extract_sqa(df: DataFrame) -> DataFrame:
        """Extract SQA report URL and badge from nested Provider Component data."""
        if "sqa" not in df.columns:
            return df.withColumn("sqa_url", lit(None)).withColumn("sqa_badge", array())

        sqa_field = df.schema["sqa"]
        if not isinstance(sqa_field.dataType, StructType):
            return (
                df.withColumn("sqa_url", lit(None))
                .withColumn("sqa_badge", array())
                .drop("sqa")
            )

        df = df.withColumn("sqa_url", col("sqa.sqaURL")).withColumn(
            "sqa_badge",
            when(
                col("sqa.sqaBadge").isNotNull(),
                array(initcap(regexp_replace(col("sqa.sqaBadge"), "sqa_badge-", ""))),
            ).otherwise(array()),
        )
        return df.drop("sqa")

    @staticmethod
    def extract_license(df: DataFrame) -> DataFrame:
        """Use licenseName from nested license metadata and drop licenseURL."""
        if "license" not in df.columns:
            return df.withColumn("license", lit(None))

        license_field = df.schema["license"]
        if isinstance(license_field.dataType, StructType):
            return df.withColumn("license", col("license.licenseName"))

        return df

    @staticmethod
    def extract_alternative_ids(df: DataFrame) -> DataFrame:
        """Extract alternative PID values to a flat text field for Solr."""
        if "alternativePIDs" not in df.columns:
            return df.withColumn("alternative_ids", lit(None))

        return df.withColumn(
            "alternative_ids",
            AdapterTransformer.extract_alternative_pid_values(col("alternativePIDs")),
        ).drop("alternativePIDs")

    @staticmethod
    @udf(StringType())
    def extract_alternative_pid_values(alternative_pids):
        values = []
        for alternative_pid in alternative_pids or []:
            if isinstance(alternative_pid, str):
                values.append(alternative_pid)
                continue

            alternative_pid = AdapterTransformer._row_to_dict(alternative_pid)
            value = alternative_pid.get("pid")
            if value:
                values.append(value)

        return ", ".join(values) if values else None

    @staticmethod
    def extract_urls(df: DataFrame) -> DataFrame:
        """Normalize input URLs to the Solr url multivalue field."""
        if "url" not in df.columns:
            return df.withColumn("url", array())

        url_field = df.schema["url"]
        if isinstance(url_field.dataType, ArrayType):
            return df

        return df.withColumn(
            "url",
            when(col("url").isNotNull(), array(col("url"))).otherwise(array()),
        )

    @staticmethod
    def extract_creators(df: DataFrame) -> DataFrame:
        """Flatten creator metadata into Solr-friendly string arrays."""
        if "creators" not in df.columns:
            return (
                df.withColumn("creator_names", array())
                .withColumn("creator_identifiers", array())
                .withColumn("creator_affiliations", array())
            )

        df = (
            df.withColumn(
                "creator_names",
                AdapterTransformer.extract_creator_names(col("creators")),
            )
            .withColumn(
                "creator_identifiers",
                AdapterTransformer.extract_creator_identifiers(col("creators")),
            )
            .withColumn(
                "creator_affiliations",
                AdapterTransformer.extract_creator_affiliations(col("creators")),
            )
        )
        return df.drop("creators")

    @staticmethod
    def _row_to_dict(value):
        if hasattr(value, "asDict"):
            return value.asDict(recursive=True)
        if isinstance(value, dict):
            return value
        return {}

    @staticmethod
    @udf(ArrayType(StringType()))
    def extract_creator_names(creators):
        names = []
        for creator in creators or []:
            creator = AdapterTransformer._row_to_dict(creator)
            name = " ".join(
                part
                for part in (
                    creator.get("firstName"),
                    creator.get("lastName"),
                )
                if part
            )
            if name:
                names.append(name)
        return names

    @staticmethod
    @udf(ArrayType(StringType()))
    def extract_creator_identifiers(creators):
        identifiers = []
        for creator in creators or []:
            creator = AdapterTransformer._row_to_dict(creator)
            for pid in creator.get("PIDs") or []:
                pid = AdapterTransformer._row_to_dict(pid)
                for key in ("creatorPID", "pid", "id", "value"):
                    value = pid.get(key)
                    if value:
                        identifiers.append(value)
                        break
        return identifiers

    @staticmethod
    @udf(ArrayType(StringType()))
    def extract_creator_affiliations(creators):
        affiliations = []
        for creator in creators or []:
            creator = AdapterTransformer._row_to_dict(creator)
            for affiliation in creator.get("affiliations") or []:
                affiliation = AdapterTransformer._row_to_dict(affiliation)
                value = affiliation.get("affiliationName") or affiliation.get("name")
                if value:
                    affiliations.append(value)
        return affiliations

    @staticmethod
    def clean_description(df: DataFrame) -> DataFrame:
        """Remove HTML tags and nbsp from description."""
        if "description" not in df.columns:
            return df

        return df.withColumn(
            "description",
            trim(
                regexp_replace(
                    regexp_replace(col("description"), r"<\/?[a-zA-Z][^>]*>", ""),
                    r"&nbsp;|\u00A0",
                    " ",
                )
            ),
        )
