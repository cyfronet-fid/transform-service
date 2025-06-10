"""Expected db adapter schema"""

from datetime import datetime
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
        code_repository_url (AnyHttpUrl):
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
        releases (List[str]):
            A list of release versions or information.
        tagline (Optional[str]):
            A brief tagline or summary for the adapter.
        title (str):
            The title/name of the adapter.
        type (str):
            Data type = "adapter".
        version (str):
            The current version of the adapter.
    """

    admins: Optional[List[str]]
    catalogues: List[str]
    changelog: List[str]
    code_repository_url: AnyHttpUrl
    description: str
    documentation_url: AnyHttpUrl
    id: str
    last_update: datetime
    license: str
    logo: Optional[str]
    node: Optional[str]
    programming_language: str
    related_guidelines: Optional[List[str]]
    related_services: Optional[List[str]]
    releases: List[str]
    tagline: Optional[str]
    title: str
    type: str
    version: str

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
