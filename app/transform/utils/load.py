import json
from logging import getLogger
from typing import Type

from pydantic import BaseModel
from pyspark.sql import DataFrame, SparkSession

from app.services.solr.validate.schema.validate import (
    is_pydantic_schema,
    validate_pydantic_data,
    validate_schema,
)

logger = getLogger(__name__)


def load_file_data(spark: SparkSession, data_path: str, _format: str = "json"):
    """Load data based on the provided data path"""
    return spark.read.format(_format).load(data_path)


def load_request_data(
    spark: SparkSession,
    data: dict | list[dict],
    input_exp_sch: dict | Type[BaseModel],
    type_: str,
) -> DataFrame:
    """Load input data into pyspark dataframe, validate its schema"""
    try:
        if is_pydantic_schema(input_exp_sch):
            validate_pydantic_data(
                data, input_exp_sch, collection=type_, source="input"
            )
        else:
            df_for_validation = spark.read.json(
                spark.sparkContext.parallelize([json.dumps(data)])
            )
            validate_schema(
                df_for_validation,
                input_exp_sch,
                collection=type_,
                source="input",
            )
    except AssertionError:
        logger.warning(
            f"Schema validation of raw input data for type={type_} has failed. Input schema is different than excepted"
        )
    df = spark.read.json(spark.sparkContext.parallelize([json.dumps(data)]))
    return df
