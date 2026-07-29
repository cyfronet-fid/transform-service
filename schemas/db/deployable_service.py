"""Deployable Service expected db schema"""

from datetime import datetime
from typing import List, Optional

from pydantic import AnyHttpUrl, BaseModel


class DeployableServiceDBSchema(BaseModel):
    """
    Pydantic model representing the expected db schema for a deployable service.

    Attributes:
        abbreviation (str):
            The abbreviation of the deployable service.
        catalogues (List[str]):
            A list of catalogues associated with the deployable service.
        creator_identifiers (List[str]):
            A list of creator identifiers (URLs) extracted from the creators field.
        creator_names (List[str]):
            A list of creator names extracted from the creators field.
        creators_searchable (List[str]):
            A searchable text field combining creator names and affiliations.
        description (str):
            A detailed description of the deployable service.
        id (str):
            Unique identifier for the deployable service.
        keywords (List[str]):
            A list of keywords/tags categorizing the deployable service.
        last_update (Optional[datetime]):
            The date when the deployable service was last updated.
        license (str):
            The name of the software license associated with the deployable service.
        license_url (str):
            The URL pointing to the software license details.
        node (str):
            Name of the node associated with the deployable service.
        pid (str):
            Persistent identifier for the deployable service.
        publication_date (datetime):
            The date when the deployable service was published.
        public_contacts (List[str]):
            Public contact email addresses associated with the deployable service.
        resource_organisation (str):
            The organisation responsible for the deployable service.
        scientific_domains (List[str]):
            A list of scientific domains associated with the deployable service.
        slug (str):
            The slug (URL-friendly identifier) for the deployable service.
        status (str):
            The status of the deployable service.
        synchronized_at (Optional[datetime]):
            The date and time when the deployable service was last synchronized.
        tagline (str):
            A tagline for the deployable service.
        title (str):
            The title of the deployable service.
        type (str):
            Data type = "deployable service".
        updated_at (datetime):
            The date and time when the deployable service was last updated.
        upstream_id (int):
            The upstream ID of the deployable service.
        url (AnyHttpUrl):
            The URL where the deployable service can be accessed or downloaded.
        version (str):
            The version of the deployable service.
    """

    abbreviation: str
    catalogues: List[str]
    creator_identifiers: List[str]
    creator_names: List[str]
    creators_searchable: List[str]
    description: str
    id: str
    keywords: List[str]
    last_update: Optional[datetime]
    license: str
    license_url: str
    node: str
    pid: str
    publication_date: datetime
    public_contacts: List[str]
    resource_organisation: str
    scientific_domains: List[str]
    slug: str
    status: str
    synchronized_at: Optional[datetime]
    tagline: str
    title: str
    type: str
    updated_at: datetime
    upstream_id: int
    url: AnyHttpUrl
    version: str
