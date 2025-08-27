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
        last_update (date):
            The date when the adapter was last updated. Used in sorting.
        license (str):
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
        releases (List[str]):
            A list of release versions or information. Used in detail page.
        keywords (Optional[str]):
            A brief tagline or summary for the adapter. Used in detail page.
        title (str):
            The title/name of the adapter. Used in searching.
        type (str):
            Data type = "adapter". Used in filters.
        version (str):
            The current version of the adapter. Used in detail page.
    """

    catalogues: List[str]
    changelog: List[str]
    repository: str
    description: str
    documentation_url: str
    id: str
    last_update: date
    license: str
    logo: Optional[str]
    node: Optional[str]
    programming_language: str
    related_guidelines: Optional[List[str]]
    related_services: Optional[List[str]]
    releases: List[str]
    keywords: Optional[str]
    title: str
    type: str
    version: str

    """
    Transformations necessary to convert AdapterInputSchema to AdapterSESchema:
        - add type = "adapter"
            - get_node_pretty_name
            - ts_to_iso
        - rename:
            "catalogueId": "catalogues",
            "changeLog": "changelog",
            "repository": "code_repository_url",
            "documentation": "documentation_url",
            "lastUpdate": "last_update",
            "programmingLanguage": "programming_language",
            "name": "title",
        - delete:
            "admins" (not used)
        - cast:
            df.withColumn("catalogues", array(col("catalogueId")))
            df.withColumn("changelog", split(col("changeLog"), ","))
            transform_date(df, "last_update", "yyyy-MM-dd'T'HH:mm:ss.SSS'Z'")
        - extract from linkedResource:
            - if linkedResource.type == "Guideline": add to related_guidelines
            - if linkedResource.type == "Service": add to related_services
    """
