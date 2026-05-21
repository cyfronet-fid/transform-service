"""Expected db adapter schema"""

from datetime import date
from typing import List, Optional

from pydantic import AnyHttpUrl, BaseModel


class AdapterDBSchema(BaseModel):
    """
    Pydantic model representing the expected db schema for adapter.

    Attributes:
        admins (Optional[List[str]]):
            A list of administrators for the adapter.
        catalogues (List[str]):
            The catalogue identifiers for the adapter (cast to array).
        changelog (List[str]):
            The change log information (cast to array).
        repository (AnyHttpUrl):
            URL to the adapter's source code repository.
        description (str):
            A detailed description of the adapter.
        documentation_url (AnyHttpUrl):
            URL to the adapter's documentation.
        id (str):
            The unique identifier of the adapter.
        last_update (datetime):
            The last update date of the adapter (ISO 8601 format).
        license (str):
            The license under which the adapter is provided.
        logo (Optional[str]):
            URL to the adapter's logo image.
        node (Optional[str]):
            Name of the node associated with the adapter (pretty name).
        programming_language (str):
            The programming language used for the adapter.
        related_guidelines (Optional[List[str]]):
            A list of related guidelines for the adapter.
        related_services (Optional[List[str]]):
            A list of related services for the adapter.
        package (List[str]):
            A list of release/package URLs.
        keywords (Optional[str]):
            A brief tagline or summary for the adapter.
        sqa_badge (Optional[List[str]]):
            Software quality assurance badge labels.
        sqa_url (Optional[str]):
            Software quality assurance report URL.
        title (str):
            The title/name of the adapter.
        type (str):
            Data type = "adapter".
        version (str):
            The current version of the adapter.
    """

    catalogues: List[str]
    changelog: List[str]
    repository: AnyHttpUrl
    description: str
    documentation_url: AnyHttpUrl
    id: str
    publication_date: Optional[date]
    last_update: Optional[date]
    license: Optional[str]
    logo: Optional[str]
    node: Optional[str]
    programming_language: str
    related_guidelines: Optional[List[str]]
    related_services: Optional[List[str]]
    package: List[str]
    keywords: Optional[str]
    sqa_badge: Optional[List[str]]
    sqa_url: Optional[str]
    title: str
    type: str
    version: str
    url: List[str]
    alternative_ids: Optional[str]
    resource_owner: str
    creator_names: Optional[List[str]]
    creator_identifiers: Optional[List[str]]
    creator_affiliations: Optional[List[str]]
    public_contacts: List[str]

    """
    Transformations necessary to convert AdapterInputSchema to AdapterDBSchema:
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
        - cast:
            df.withColumn("catalogues", array(col("catalogueId")))
            df.withColumn("changelog", split(col("changeLog"), ","))
            transform_date(df, "last_update", "yyyy-MM-dd'T'HH:mm:ss.SSS'Z'")
        - extract from linkedResource:
            - if linkedResource.type == "Guideline": add to related_guidelines
            - if linkedResource.type == "Service": add to related_services
    """
