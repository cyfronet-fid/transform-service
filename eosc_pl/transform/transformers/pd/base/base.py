# pylint: disable=line-too-long, too-many-arguments), invalid-name
"""Base transformer of pandas df"""
import json
import logging
from abc import ABC, abstractmethod

from pandas import DataFrame
from transform.utils.consts import AUTHOR_NAMES, AUTHOR_NAMES_TG, KEYWORDS, KEYWORDS_TG

logger = logging.getLogger(__name__)


class TransformerException(Exception):
    pass


class BaseDataverseTransformer(ABC):
    """Base pandas transformer class"""

    def __init__(
        self,
        desired_type: str,
        cols_to_drop: tuple[str, ...] | None,
        cols_to_rename: dict[str, str] | None,
    ):
        self.type = desired_type
        self._cols_to_drop = cols_to_drop
        self._cols_to_rename = cols_to_rename

    def __call__(self, df: DataFrame) -> DataFrame:
        """Transform resources"""
        try:
            df = self.transform(df)
        except Exception as e:
            logger.error(f"transform phase failed: {e}")
            raise TransformerException from e
        try:
            df = self.apply_common_trans(df)
        except Exception as e:
            logger.error(f"common_trans fase failed: {e}")
            raise TransformerException from e
        try:
            df = self.cast_columns(df)
        except Exception as e:
            logger.error(f"cast_columns fase failed: {e}")
            raise TransformerException from e
        return df

    def __repr__(self):
        return f"{self.__class__.__name__}({self.type})"

    def apply_common_trans(self, df: DataFrame) -> DataFrame:
        """Apply common transformations"""
        self.add_tg_fields(df)
        if self._cols_to_drop:
            df = self.drop_columns(df)
        if self._cols_to_rename:
            self.rename_cols(df)

        return df

    def drop_columns(self, df: DataFrame) -> DataFrame:
        """Drop specified columns from a pandas DataFrame."""
        return df.drop(columns=self._cols_to_drop)

    def rename_cols(self, df: DataFrame) -> None:
        """Rename columns based on the mappings dict"""
        df.rename(columns=self._cols_to_rename, inplace=True)

    @staticmethod
    def serialize(df: DataFrame, cols: list[str]) -> None:
        """Serialize columns"""
        for col in cols:
            df[col] = df[col].apply(lambda x: json.dumps(x, indent=2))

    @staticmethod
    def map_str_to_arr(df: DataFrame, cols: list[str]) -> None:
        """Map string columns to array columns"""
        for col in cols:
            df[col] = [[row] for row in df[col]]

    @staticmethod
    def add_tg_fields(df: DataFrame) -> None:
        """Add text_general fields"""
        if AUTHOR_NAMES in df.columns:
            df[AUTHOR_NAMES_TG] = df[AUTHOR_NAMES]
        if KEYWORDS in df.columns:
            df[KEYWORDS_TG] = df[KEYWORDS]

    @abstractmethod
    def transform(self, df: DataFrame) -> DataFrame:
        """Apply df transformations"""
        raise NotImplementedError

    @abstractmethod
    def cast_columns(self, df: DataFrame) -> DataFrame:
        """Cast certain columns"""
        raise NotImplementedError

    @property
    @abstractmethod
    def cols_to_rename(self) -> dict[str, str] | None:
        """Columns to rename. Keys are mapped to the values"""
        raise NotImplementedError
