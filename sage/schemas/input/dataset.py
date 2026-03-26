from typing import List, Optional

from pydantic import BaseModel, Field, HttpUrl


class Publisher(BaseModel):
    id: Optional[str] = Field(None, alias="@id")
    name: Optional[str] = None

    model_config = {"extra": "allow"}


class Metadata(BaseModel):
    abstract: Optional[str] = Field(None, alias="dct:abstract")
    issued: Optional[str] = Field(None, alias="dct:issued")
    updated: Optional[str] = Field(None, alias="dct:updated")
    language: Optional[str] = Field(None, alias="dct:language")

    license: List[str] = Field(default_factory=list, alias="dct:license")

    publisher: Optional[Publisher] = Field(None, alias="dct:publisher")

    data_quality: Optional[str] = Field(None, alias="dcat:dataQuality")
    granularity: Optional[str] = Field(None, alias="dcat:granularity")
    keyword: List[str] = Field(default_factory=list, alias="dcat:keyword")

    model_config = {"extra": "allow"}


class Dataset(BaseModel):
    id_jsonld: str = Field(..., alias="@id")  # only required field

    type: Optional[str] = Field(None, alias="@type")
    version: Optional[str] = None
    name: Optional[str] = None

    metadata: Optional[Metadata] = None

    id: Optional[str] = None
    contenttype: Optional[str] = None
    baseUrl: Optional[HttpUrl] = None

    model_config = {
        "populate_by_name": True,
        "extra": "allow",
    }
