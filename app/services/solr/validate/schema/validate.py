# pylint: disable=line-too-long, invalid-name, logging-fstring-interpolation
"""Validate transformation"""
import logging
from typing import Literal

import pandas as pd
from pydantic import BaseModel, ValidationError
from pyspark.sql import DataFrame as SparkDataFrame

logger = logging.getLogger(__name__)


def validate_schema(
    df: SparkDataFrame | pd.DataFrame,
    pydantic_model: BaseModel,
    collection: str,
    source: Literal["input", "output"],
) -> None:
    """Validate DataFrame against the Pydantic model schema."""
    if isinstance(df, SparkDataFrame):
        validate_spark_schema(df, pydantic_model, collection, source)
    elif isinstance(df, pd.DataFrame):
        validate_pandas_schema(df, pydantic_model, collection, source)
    else:
        logger.warning("Unsupported DataFrame type: %s", type(df))


def validate_partition(partition, pydantic_model: BaseModel):
    """Validate a partition of data against the Pydantic model."""
    errors = set()
    for row in partition:
        try:
            pydantic_model.parse_obj(row.asDict())
        except ValidationError as e:
            error_json = e.json()
            errors.add(error_json)
    return list(errors)


def validate_spark_schema(
    df: SparkDataFrame,
    pydantic_model: BaseModel,
    collection: str,
    source: Literal["input", "output"],
) -> None:
    """Validate Spark DataFrame against Pydantic model schema."""
    errors = df.rdd.mapPartitions(
        lambda partition: validate_partition(partition, pydantic_model)
    ).collect()

    all_errors = [
        err
        for partition_errors in errors
        for err in partition_errors
        if partition_errors
    ]

    if all_errors:
        unique_errors = list(set(all_errors))
        logger.warning(
            "%s - %s schema validation failure. Distinct validation errors: %s",
            collection,
            source,
            unique_errors,
        )


def validate_pandas_schema(
    df: pd.DataFrame,
    pydantic_model: BaseModel,
    collection: str,
    source: Literal["input", "output"],
) -> None:
    """Validate Pandas DataFrame against Pydantic model schema."""
    errors = set()
    for _, row in df.iterrows():
        try:
            pydantic_model.parse_obj(row.asDict())
        except ValidationError as e:
            errors.add(e.json())

    if errors:
        logger.warning(
            "%s - %s schema validation failure. Validation errors: %s",
            collection,
            source,
            errors,
        )
