# pylint: disable=undefined-variable, cyclic-import
"""Import transformations"""
from settings import Repository

from .repod.dataset import RepodDatasetTransformer
from .rodbuk.dataset import RodbukDatasetTransformer

__all__ = [
    "transformers",
]

transformers = {
    Repository.RODBUK: RodbukDatasetTransformer,
    Repository.REPOD: RepodDatasetTransformer,
}
