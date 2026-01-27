from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field, HttpUrl


class Distribution(BaseModel):
    context: Optional[str] = Field(alias="@context")
    type: Optional[str] = Field(alias="@type")
    download_url: HttpUrl = Field(alias="downloadURL")
    format: Optional[str] = None


class ContactPoint(BaseModel):
    context: Optional[str] = Field(alias="@context")
    type: Optional[str] = Field(alias="@type")
    full_name: str = Field(alias="fn")
    email: EmailStr = Field(alias="hasEmail")


class Publisher(BaseModel):
    context: Optional[str] = Field(alias="@context")
    type: Optional[str] = Field(alias="@type")
    name: str


class DatasetRecord(BaseModel):
    context: Optional[str] = Field(alias="@context")
    type: Optional[str] = Field(alias="@type")
    distribution: List[Distribution]
    access_level: str = Field(alias="accessLevel")
    contact_point: ContactPoint = Field(alias="contactPoint")
    description: str
    identifier: str
    issued: str
    keywords: List[str]
    language: Optional[str] = None
    modified: str
    publisher: Publisher
    spatial: Optional[str] = None
    temporal: Optional[str] = None
    title: str

    class Config:
        allow_population_by_field_name = True
        extra = "ignore"
