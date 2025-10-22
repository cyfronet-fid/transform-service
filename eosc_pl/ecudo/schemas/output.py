from typing import List

from pydantic import BaseModel, Field


class EcudoRecord(BaseModel):
    id: str
    type: str = "dataset"
    title: str | None
    description: str | None
    language: str | None
    publication_date: str | None
    publication_year: str | None
    updated_at: str | None
    publisher: str | None
    spatial: str | None
    temporal: str | None
    keywords: List[str] = Field(default_factory=list)
    keywords_tg: List[str] = Field(default_factory=list)
    url: List[str] = Field(default_factory=list)  # converted to string
    datasource_pids: List[str] = Field(
        default_factory=lambda: ["eosc.gdansk_tech.ecudo"]
    )
    best_access_right: str = "Open access"
