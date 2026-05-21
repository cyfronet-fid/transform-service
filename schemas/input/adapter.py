"""Input adapter expected schema for adapters"""

from datetime import date
from typing import Any, List, Optional

from pydantic import AnyHttpUrl, BaseModel


class LinkedResource(BaseModel):
    """
    Model representing a linked resource.

    Attributes:
        resource_type (str):
            The type of the linked resource.
        id (str):
            The unique identifier of the linked resource.
    """

    resource_type: str
    id: str


class Creator(BaseModel):
    """Model representing adapter creator contact data."""

    firstName: str
    lastName: str
    email: str
    role: Optional[str] = None
    PIDs: Optional[List[Any]] = None
    affiliations: Optional[List[Any]] = None


class SQA(BaseModel):
    """Software quality assurance metadata."""

    sqaURL: Optional[AnyHttpUrl] = None
    sqaBadge: Optional[str] = None


class License(BaseModel):
    """Adapter license metadata from Provider Component."""

    licenseName: str
    licenseURL: Optional[AnyHttpUrl] = None


class AdapterInputSchema(BaseModel):
    """
    Pydantic model representing the expected input schema for adapters.

    Attributes:
        id (str):
            The unique identifier of the adapter.
        name (str):
            The name of the adapter.
        nodePID (str):
            Identifier of the node associated with the adapter.
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
        package (List[AnyHttpUrl]):
            A list of release/package URLs.
        programmingLanguage (str):
            The programming language used for the adapter.
        license (Optional[License]):
            The license under which the adapter is provided.
        version (str):
            The current version of the adapter.
        changeLog (Union[str, AnyHttpUrl]):
            The change log information, either as text or URL.
        lastUpdate (date):
            The last update date of the adapter.
    """

    id: str
    name: str
    urls: Optional[List[AnyHttpUrl]] = None
    alternativePIDs: Optional[List[Any]] = None
    nodePID: Optional[str] = None
    description: str
    publishingDate: date
    type: str
    resourceOwner: str
    linkedResource: LinkedResource
    tagline: Optional[str] = None
    logo: Optional[AnyHttpUrl] = None
    documentation: AnyHttpUrl
    repository: AnyHttpUrl
    package: List[AnyHttpUrl]
    programmingLanguage: str
    license: Optional[License] = None
    version: str
    changeLog: str
    lastUpdate: date
    creators: List[Creator]
    publicContacts: List[str]
    sqa: Optional[SQA] = None
