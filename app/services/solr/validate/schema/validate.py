# pylint: disable=line-too-long, invalid-name, logging-fstring-interpolation
"""Validate transformation"""

# TODO: Improve schema validation #110

import logging
from itertools import zip_longest
from typing import KeysView, Literal, Type

from pydantic import BaseModel, ValidationError
from pyspark.sql import DataFrame, Row

logger = logging.getLogger(__name__)


def is_pydantic_schema(expected_schema) -> bool:
    """Check whether expected schema is a Pydantic model class."""
    return isinstance(expected_schema, type) and issubclass(expected_schema, BaseModel)


def validate_pydantic_data(
    data: dict | list[dict],
    expected_schema: Type[BaseModel],
    collection: str,
    source: Literal["input", "output"],
) -> None:
    """Validate raw dict data against a Pydantic schema."""
    records = data if isinstance(data, list) else [data]
    errors = []

    for index, record in enumerate(records):
        try:
            expected_schema.model_validate(record)
        except ValidationError as err:
            errors.append({"index": index, "errors": err.errors(), "record_id": record.get("id"),
                    "record_name": record.get("name"),})

    if errors:
        # logger.warning(
        #     "%s - %s Pydantic schema validation failure. Errors: %s",
        #     collection,
        #     source,
        #     errors,
        # )

        # logger.warning(
        #     "%s - %s Pydantic schema validation failure. Errors count: %i",
        #     collection,
        #     source,
        #     len(errors),
        # )
        # # logger.warning("First error: %s", errors[0])
        #
        # logger.warning("Error keys: ")
        # logger.warning(type(errors))
        # for error in errors[:10]:
        #     logger.warning(f"\n\n\n\n\nError {error['index']}--------------------")
        #     # del error["input"]
        #     for e in error["errors"]:
        #         # logger.warning(e.keys())
        #         id_value = e['input']['id']
        #         name = e['input']['name']
        #         logger.warning(f"Error for id: {id_value} name: {name}")
        #         del e["input"]
        #         logger.warning(e)
        #         # logger.warning(f"Type: {e['type']}, ")
        #     # logger.warning(error["errors"]["type"])
        #     # logger.warning(error["errors"]["loc"])
        #     # logger.warning(error["errors"]["message"])
        for record_error in errors[:20]:
            logger.warning(
                "\nRecord index=%s id=%s name=%s",
                record_error["index"],
                record_error["record_id"],
                record_error["record_name"],
            )

            for err in record_error["errors"]:
                field = ".".join(str(x) for x in err["loc"])

                logger.warning(
                    "  field=%s | type=%s | msg=%s",
                    field,
                    err["type"],
                    err["msg"],
                )


def validate_pydantic_schema(
    df: DataFrame,
    expected_schema: Type[BaseModel],
    collection: str,
    source: Literal["input", "output"],
) -> None:
    """Validate DataFrame rows against a Pydantic schema."""
    errors = []

    for index, row in enumerate(df.toLocalIterator()):
        record = row_to_dict(row)
        try:
            expected_schema.model_validate(record)
        except ValidationError as err:
            errors.append({"index": index, "errors": err.errors()})

    if errors:
        logger.warning(
            "%s - %s Pydantic schema validation failure. Errors: %s",
            collection,
            source,
            errors,
        )


def row_to_dict(value):
    """Convert Spark Rows recursively into plain Python containers."""
    if isinstance(value, Row):
        return {key: row_to_dict(val) for key, val in value.asDict().items()}
    if isinstance(value, list):
        return [row_to_dict(item) for item in value]
    if isinstance(value, tuple):
        return tuple(row_to_dict(item) for item in value)
    if isinstance(value, dict):
        return {key: row_to_dict(val) for key, val in value.items()}
    return value


def validate_schema(
    df: DataFrame,
    expected_schema: dict[str, list[str] | str] | Type[BaseModel],
    collection: str,
    source: Literal["input", "output"],
) -> None:
    """Check whether pyspark dataframe data schema is the same as expected"""
    if is_pydantic_schema(expected_schema):
        validate_pydantic_schema(df, expected_schema, collection, source)
        return

    # Assumption: schemas are sorted alphabetically
    df = df.select(*sorted(df.columns))  # Sort pyspark dataframe
    expected_schema = sort_dict_schemas(expected_schema)  # Sort expected schema

    validate_column_names(df.columns, expected_schema.keys(), collection, source)
    validate_column_types(df, expected_schema, collection, source)


def validate_column_names(
    actual_columns: list[str],
    expected_columns: KeysView[str],
    collection: str,
    source: Literal["input", "output"],
) -> None:
    """Validate that column names match"""
    cols_diff = set(actual_columns) ^ set(expected_columns)
    if cols_diff:
        logger.warning(
            f"{collection} - {source} schema validation failure. Column names mismatch. Difference: {cols_diff}"
        )


def validate_column_types(
    df: DataFrame,
    expected_schema: dict[str, list[str] | str],
    collection: str,
    source: Literal["input", "output"],
) -> None:
    """Validate that column types match"""
    actual_types = [column.dataType.simpleString() for column in df.schema.fields]
    differences = get_schema_differences(df.columns, actual_types, expected_schema)
    if differences:
        logger.warning(
            f"{collection} - {source} schema validation failure. Column types mismatch. Differences: {differences}"
        )


def validate_pd_schema(
    df: DataFrame,
    expected_schema: dict[str, list[str] | str],
    collection: str,
    source: Literal["input", "output"],
) -> None:
    """Validate Pandas schema"""
    # Assumption: schemas are sorted alphabetically
    df = df.reindex(sorted(df.columns), axis=1)  # Sort pandas df
    expected_schema = sort_dict_schemas(expected_schema)  # Sort expected schema

    validate_column_names(df.columns, expected_schema.keys(), collection, source)
    validate_pd_column_types(df, expected_schema, collection, source)


def validate_pd_column_types(
    df: DataFrame,
    expected_schema: dict[str, list[str] | str],
    collection: str,
    source: Literal["input", "output"],
) -> None:
    """Validate Pandas column types"""
    actual_schema = get_pd_df_schema(df)
    differences = get_schema_differences(
        list(actual_schema.keys()), list(actual_schema.values()), expected_schema
    )
    if differences:
        logger.warning(
            f"{collection} - {source} schema validation failure. Column types mismatch. Differences: {differences}"
        )


def get_pd_df_schema(df: DataFrame) -> dict:
    """Get Pandas data schema"""

    def get_column_type(column):
        for val in df[column]:
            if val is not None:
                return type(val).__name__
        return "NoneType"  # If all values are None

    return {col: get_column_type(col) for col in df.columns}


def is_type_match(actual_type: str, expected_type: list[str] | str) -> bool:
    """Check if the actual type matches the expected type(s)"""
    if isinstance(expected_type, list):
        return actual_type in expected_type or actual_type == "void"
    else:
        return actual_type == expected_type or actual_type == "void"


def get_schema_differences(
    columns: list[str],
    actual_schema: list[str],
    expected_schema: dict[str, list[str] | str],
) -> dict[str, dict[str, list[str] | str]]:
    """Print differences between schemas types"""
    differences = {}

    for col, actual_sch in zip_longest(columns, actual_schema):
        expected_sch = expected_schema[col]
        if not is_type_match(actual_sch, expected_sch):
            differences[col] = {"ACTUAL": actual_sch, "EXPECTED": expected_sch}
    return differences


def sort_dict_schemas(expected_schema: dict) -> dict:
    """Sort expected dict schema"""
    return {k: expected_schema[k] for k in sorted(expected_schema)}
