"""Input adapter expected schema for adapters"""

from datetime import datetime
from typing import List, Optional, Union

from pydantic import AnyHttpUrl, BaseModel


class LinkedResource(BaseModel):
    """
    Model representing a linked resource.

    Attributes:
        type (str):
            The type of the linked resource ("Service" or "Guideline").
        id (str):
            The unique identifier of the linked resource.
    """

    type: str
    id: str


class AdapterInputSchema(BaseModel):
    """
    Pydantic model representing the expected input schema for adapters.

    Attributes:
        id (str):
            The unique identifier of the adapter.
        name (str):
            The name of the adapter.
        catalogueId (str):
            The catalogue identifier for the adapter.
        node (Optional[str]):
            Name of the node associated with the adapter.
        description (str):
            A detailed description of the adapter.
        linkedResource (LinkedResource):
            The resource that this adapter is linked to.
        tagline (Optional[str]):
            A brief tagline or summary for the adapter.
        logo (Optional[AnyHttpUrl]):
            URL to the adapter's logo image.
        documentation (AnyHttpUrl):
            URL to the adapter's documentation.
        repository (AnyHttpUrl):
            URL to the adapter's source code repository.
        releases (List[str]):
            A list of release versions or information.
        programmingLanguage (str):
            The programming language used for the adapter.
        license (str):
            The license under which the adapter is provided.
        version (str):
            The current version of the adapter.
        changeLog (Union[str, AnyHttpUrl]):
            The change log information, either as text or URL.
        lastUpdate (datetime):
            The last update date of the adapter (ISO 8601 format).
        admins (Optional[List[str]]):
            A list of administrators for the adapter.
    """

    id: str
    name: str
    catalogueId: str
    node: Optional[str]
    description: str
    linkedResource: LinkedResource
    tagline: Optional[str]
    logo: Optional[AnyHttpUrl]
    documentation: AnyHttpUrl
    repository: AnyHttpUrl
    releases: List[str]
    programmingLanguage: str
    license: str
    version: str
    changeLog: Union[str, AnyHttpUrl]
    lastUpdate: datetime
    admins: Optional[List[str]]
