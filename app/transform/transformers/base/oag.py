# pylint: disable=line-too-long, wildcard-import, unused-wildcard-import
"""Transform OAG resources"""
import logging
from abc import abstractmethod

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import array, col, lit, udf, year, when
from pyspark.sql.types import (
    ArrayType,
    BooleanType,
    IntegerType,
    StringType,
    StructField,
    StructType,
)

from app.services.mp_pc.node import get_node_id_name_mapping
from app.settings import settings
from app.transform.transformers.base.base import BaseTransformer
from app.transform.utils.common import (
    check_type,
    create_open_access,
    create_unified_categories,
    harvest_author_names_and_pids,
    harvest_country,
    harvest_data_source,
    harvest_eosc_if,
    harvest_exportation,
    harvest_funder,
    harvest_pids,
    harvest_popularity,
    harvest_project_ids,
    harvest_related_organisations,
    harvest_relations,
    harvest_research_community,
    harvest_scientific_domains,
    harvest_sdg,
    harvest_url_and_document_type,
    map_best_access_right,
    map_language,
    map_publisher,
    simplify_indicators,
    simplify_language,
    transform_date,
)
from app.transform.utils.utils import sort_schema
from schemas import *
from schemas.properties.data import *

logger = logging.getLogger(__name__)


class OagBaseTransformer(BaseTransformer):
    """Transformer used to transform OAG resources"""

    def __init__(
        self,
        desired_type: str,
        cols_to_add: tuple[str, ...] | None,
        cols_to_drop: tuple[str, ...] | None,
        exp_output_schema: dict,
        spark: SparkSession,
    ):
        super().__init__(
            desired_type,
            cols_to_add,
            cols_to_drop,
            self.cols_to_rename,
            exp_output_schema,
            spark,
        )
        self.catalogue = "eosc"

    def apply_simple_trans(self, df: DataFrame) -> DataFrame:
        """Apply simple transformations.
        Simple in a way that there is a possibility to manipulate the main dataframe
        without a need to create another dataframe and merging"""
        check_type(df, desired_type=self.type)
        df = df.withColumn("catalogues", array(lit(self.catalogue)))
        df = df.withColumn("catalogue", lit(self.catalogue))  # TODO delete
        df = self.rename_cols(df)
        df = self.map_node_ids_to_names(df)
        df = simplify_language(df)
        df = simplify_indicators(df)
        df = map_publisher(df)
        return df

    def apply_complex_trans(self, df: DataFrame) -> DataFrame:
        """Harvest oag properties that requires more complex transformations
        Basically from those harvested properties there will be created another dataframe
        which will be later on merged with the main dataframe"""
        df = map_best_access_right(df, self.harvested_properties, self.type)
        create_open_access(self.harvested_properties)
        df = map_language(df, self.harvested_properties)
        harvest_author_names_and_pids(df, self.harvested_properties)
        harvest_scientific_domains(df, self.harvested_properties)
        harvest_sdg(df, self.harvested_properties)
        harvest_funder(df, self.harvested_properties)
        harvest_url_and_document_type(df, self.harvested_properties)
        harvest_pids(df, self.harvested_properties)
        harvest_country(df, self.harvested_properties)
        harvest_research_community(df, self.harvested_properties)
        harvest_relations(df, self.harvested_properties)
        harvest_eosc_if(df, self.harvested_properties)
        harvest_popularity(df, self.harvested_properties)
        create_unified_categories(df, self.harvested_properties)
        harvest_exportation(df, self.harvested_properties)
        harvest_data_source(df, self.harvested_properties)
        harvest_related_organisations(df, self.harvested_properties)
        harvest_project_ids(df, self.harvested_properties)

        return df

    @property
    def harvested_schema(self) -> StructType:
        """Schema of harvested properties"""
        return sort_schema(
            StructType(
                [
                    StructField(AUTHOR_NAMES, ArrayType(StringType()), True),
                    StructField(AUTHOR_PIDS, ArrayType(ArrayType(StringType())), True),
                    StructField(BEST_ACCESS_RIGHT, StringType(), True),
                    StructField(COUNTRY, ArrayType(StringType()), True),
                    StructField(DATA_SOURCE, ArrayType(StringType()), True),
                    StructField(DOCUMENT_TYPE, ArrayType(StringType()), True),
                    StructField(DOI, ArrayType(StringType()), True),
                    StructField(EOSC_IF, ArrayType(StringType()), True),
                    StructField(EXPORTATION, ArrayType(StringType()), True),
                    StructField(FUNDER, ArrayType(StringType()), True),
                    StructField(LANGUAGE, ArrayType(StringType()), True),
                    StructField(OPEN_ACCESS, BooleanType(), True),
                    StructField(PIDS, StringType(), True),
                    StructField(POPULARITY, IntegerType(), True),
                    StructField(
                        RELATED_ORGANISATION_TITLES, ArrayType(StringType()), True
                    ),
                    StructField(RELATED_PROJECT_IDS, ArrayType(StringType()), True),
                    StructField(RELATIONS, ArrayType(StringType()), True),
                    StructField(RELATIONS_LONG, ArrayType(StringType()), True),
                    StructField(RESEARCH_COMMUNITY, ArrayType(StringType()), True),
                    StructField(SCIENTIFIC_DOMAINS, ArrayType(StringType()), True),
                    StructField(SDG, ArrayType(StringType()), True),
                    StructField(UNIFIED_CATEGORIES, ArrayType(StringType()), True),
                    StructField(URL, ArrayType(StringType()), True),
                ]
            )
        )

    @staticmethod
    def cast_columns(df: DataFrame) -> DataFrame:
        """Cast certain OAG columns"""
        df = transform_date(df, "publication_date", "yyyy-MM-dd")
        df = df.withColumn("publication_year", year(col("publication_date")))
        df = df.withColumn("node", col("node")[0])  # TODO switch to an array

        return df

    @property
    def cols_to_rename(self) -> dict[str, str]:
        """Columns to rename. Keys are mapped to the values"""
        return {
            "bestaccessright": "best_access_right",
            "documentationUrl": "documentation_url",
            "programmingLanguage": "programming_language",
            "publicationdate": "publication_date",
            "maintitle": "title",
            "fulltext": "direct_url",
            "labels": "node",
        }

    @property
    @abstractmethod
    def cols_to_add(self) -> tuple[str, ...]:
        """Add those columns to the dataframe"""
        raise NotImplementedError

    @property
    @abstractmethod
    def cols_to_drop(self) -> tuple[str, ...]:
        """Drop those columns to the dataframe"""
        raise NotImplementedError

    @staticmethod
    def map_node_ids_to_names(df: DataFrame) -> DataFrame:
        """Map node IDs in the 'node' column (list of strings) to their corresponding names using the singleton mapping.

        If a record has more than one node ID, log a warning.
        If a record has no 'node' column or it's null/empty, set it to default node name as default.
        Replaces the 'node' column with the mapped values.
        """
        DEFAULT_NODE_NAME = "EU Node"
        mapping = get_node_id_name_mapping(settings.NODE_ADDRESS)

        if not mapping:
            logger.warning("Node ID -> name mapping is empty. Skipping node mapping.")
            return df

        @udf(returnType=ArrayType(StringType()))
        def map_nodes_udf(nodes: list[str]) -> list[str]:
            # Handle missing, null, or empty node lists
            if not nodes:
                return [DEFAULT_NODE_NAME]

            if len(nodes) > 1:
                logging.warning(f"Multiple node IDs found in a row: {nodes}")

            return [mapping.get(node_id, node_id) for node_id in nodes]

        # Check if 'node' column exists, if not create it with default value
        if "node" not in df.columns:
            df = df.withColumn(
                "node", lit([DEFAULT_NODE_NAME]).cast(ArrayType(StringType()))
            )
            # No need to map since all values are already set to default
            return df
        else:
            # Handle null values in existing 'node' column by replacing with empty array
            # The UDF will then convert empty arrays to ["EU Node"]
            df = df.withColumn(
                "node", when(col("node").isNull(), array()).otherwise(col("node"))
            )

        # Apply mapping to handle actual node IDs that exist in the data
        df = df.withColumn("node", map_nodes_udf(col("node")))
        return df
