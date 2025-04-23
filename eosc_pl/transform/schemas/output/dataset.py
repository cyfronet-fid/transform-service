from typing import Optional

from pydantic import BaseModel


class PlDataset(BaseModel):
    """Model for a Dataset from Polish repositiories"""

    author_names_tg: Optional[list[str]] = None
    author_names: Optional[list[str]] = None
    citation: Optional[list[str]] = None
    citation_html: Optional[list[str]] = None
    country: list[str] = ["PL"]
    created_at: Optional[str] = None
    datasource_pids: list[str] = None
    doi: Optional[list[str]] = None
    dataverse_id: Optional[str] = None
    dataverse_name: Optional[str] = None
    publication_date: Optional[str] = None
    publication_year: Optional[int] = None
    url: Optional[list[str]] = None
    title: Optional[list[str]] = None
    type: str = "dataset"

    affiliation: Optional[list[str]] = None
    contacts: Optional[list[str]] = None
    description: Optional[list[str]] = None
    document_type: Optional[list[str]] = None
    file_count: Optional[int] = None
    funder: Optional[list[str]] = None
    id: Optional[str] = None
    keywords: Optional[list[str]] = None
    keywords_tg: Optional[list[str]] = None
    language: Optional[list[str]] = None
    license: Optional[str] = None
    major_version: Optional[int] = None
    producers: Optional[list[str]] = None
    publicationStatuses: Optional[list[str]] = None
    publications: Optional[list[str]] = None
    publisher: Optional[list[str]] = None
    scientific_domains: Optional[list[str]] = None
    storage_id: Optional[str] = None
    subjects: Optional[list[str]] = None
    updated_at: Optional[str] = None
    version_id: Optional[int] = None
    version_state: Optional[str] = None
