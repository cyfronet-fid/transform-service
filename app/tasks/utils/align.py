"""Module to align DataFrame schemas."""

from typing import List

from pyspark.sql import DataFrame
from pyspark.sql.functions import lit


def align_df_schema(df: DataFrame, required_columns: List[str]) -> DataFrame:
    """
    Ensure the Pyspark DataFrame has all the required columns in the correct order.
    Missing columns are added with null values. Required for union operations.
    """
    current_columns = set(df.columns)
    missing_columns = [col for col in required_columns if col not in current_columns]

    # Add missing columns with null values
    for col in missing_columns:
        df = df.withColumn(col, lit(None))

    # Reorder to match required column order
    df = df.select(*required_columns)
    return df
