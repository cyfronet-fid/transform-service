"""
id : id
type=dataset
url: baseUrl
version
title: name
description: metadata.abstract
issued: metadata.issued
updated: metadata.updated
language: metadata.language
license: metadata.license - moze to byc lista
publisher: metadata.publisher.name
keywords: metadata.keyword
data_quality: metadata.dataQuality
content_type: contenttype
granularity: metadata.granularity
"""

from typing import List, Optional

from pydantic import BaseModel, HttpUrl


class Dataset(BaseModel):
    id: str

    type: str = "dataset"
    catalogue: str = None

    url: Optional[HttpUrl] = None
    version: Optional[str] = None

    title: Optional[str] = None
    description: Optional[str] = None

    issued: Optional[str] = None
    updated: Optional[str] = None

    language: Optional[str] = None
    license: List[str] = []

    publisher: Optional[str] = None

    keywords: List[str] = []

    data_quality: Optional[str] = None

    content_type: Optional[str] = None
    granularity: Optional[str] = None

    model_config = {"extra": "ignore"}
