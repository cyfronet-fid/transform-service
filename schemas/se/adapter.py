"""Adapter expected search engine schema"""

from datetime import date
from typing import List, Optional

from pydantic import BaseModel


class AdapterSESchema(BaseModel):
    """
    Pydantic model representing the expected search engine schema for adapter after transformations.

    Attributes:
        catalogues (List[str]):
            A list of catalogues associated with the adapter. Used in filters.
        changelog (List[str]):
            The change log information for the adapter. Used in detail page.
        repository (str):
            URL to the adapter's source code repository. Used in detail page.
        description (str):
            A detailed description of the adapter. Used in searching.
        documentation_url (str):
            URL to the adapter's documentation. Used in detail page.
        id (str):
            Unique identifier for the adapter.
        publication_date (date):
            The date when the adapter was published. Used in sorting.
        last_update (date):
            The date when the adapter was last updated.
        license (Optional[str]):
            The license under which the adapter is provided. Used in filters and resource view.
        logo (Optional[str]):
            URL to the adapter's logo image. Used in resource view.
        node (Optional[str]):
            Name of the node associated with the adapter. Used in filters.
        programming_language (str):
            The programming language used for the adapter. Used in filters.
        related_guidelines (Optional[List[str]]):
            A list of related guidelines associated with the adapter. Used in resource view.
        related_services (Optional[List[str]]):
            A list of related services associated with the adapter. Used in resource view.
        package (List[str]):
            A list of release/package URLs. Used in detail page.
        keywords (Optional[str]):
            A brief tagline or summary for the adapter. Used in detail page.
        title (str):
            The title/name of the adapter. Used in searching.
        type (str):
            Data type = "adapter". Used in filters.
        version (str):
            The current version of the adapter. Used in detail page.
        sqa_badge (Optional[List[str]]):
            Software quality assurance badge labels.
        sqa_url (Optional[str]):
            Software quality assurance report URL.
    """

    catalogues: List[str]
    changelog: List[str]
    repository: str
    description: str
    documentation_url: str
    id: str
    publication_date: Optional[date] = None
    last_update: Optional[date] = None
    license: Optional[str] = None
    logo: Optional[str] = None
    node: Optional[str] = None
    programming_language: str
    related_guidelines: Optional[List[str]] = None
    related_services: Optional[List[str]] = None
    package: List[str]
    keywords: Optional[str] = None
    sqa_badge: Optional[List[str]] = None
    sqa_url: Optional[str] = None
    title: str
    type: str
    version: str
    url: Optional[List[str]] = None
    alternative_ids: Optional[str] = None
    resource_owner: str
    creator_names: Optional[List[str]] = None
    creator_identifiers: Optional[List[str]] = None
    creator_affiliations: Optional[List[str]] = None
    public_contacts: List[str]
