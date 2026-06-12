"""Deployable Service expected input schema"""

from datetime import datetime
from typing import List, Optional

from pydantic import AnyHttpUrl, BaseModel

from schemas.common.creator import Creator


class DeployableServiceInputSchema(BaseModel):
    """
    Pydantic model representing the expected input schema for a deployable service.

    Attributes:
        abbreviation (str):
            The abbreviation of the deployable service.
        catalogue (str):
            The catalogue associated with the deployable service.
        creators (List[Creator]):
            A list of creators/authors of the deployable service.
        description (str):
            A detailed description of the deployable service.
        id (int):
            Unique identifier for the deployable service.
        last_update (Optional[datetime]):
            The date when the deployable service was last updated (ISO 8601 format).
        license_name (str):
            The name of the software license under which the deployable service is distributed.
        license_url (str):
            The URL pointing to the software license details.
        name (str):
            The name of the deployable service.
        node (str):
            Name of the node associated with the deployable service.
        pid (str):
            Persistent identifier for the deployable service.
        publication_date (datetime):
            The date when the deployable service was published (ISO 8601 format).
        publishing_date (datetime):
            Indicates whether the deployable service is currently published.
        public_contact_emails (List[str]):
            Public contact email addresses associated with the deployable service.
        resource_organisation (str):
            The organisation responsible for the deployable service.
        resource_type (str):
            The type of the resource "DeployableApplication".
        scientific_domains (List[str]):
            A list of scientific domains associated with the deployable service.
        slug (str):
            The slug of the deployable service.
        status (str):
            The status of the deployable service.
        synchronized_at (Optional[datetime]):
            The date and time when the deployable service was last synchronized (ISO 8601 format).
        tag_list (List[str]):
            A list of tags categorizing the deployable service.
        tagline (str):
            A tagline for the deployable service.
        updated_at (datetime):
            The date and time when the deployable service was last updated (ISO 8601 format).
        upstream_id (int):
            The upstream ID of the deployable service.
        url (AnyHttpUrl):
            The URL where the deployable service can be accessed or downloaded.
        urls (List[str]):
            A list of URLs associated with the deployable service.
        version (str):
            The version of the deployable service.
    """

    abbreviation: str
    catalogue: str
    creators: List[Creator]
    description: str
    id: int
    last_update: Optional[datetime]
    license_name: str
    license_url: str
    name: str
    node: str
    pid: str
    publication_date: datetime
    publishing_date: datetime  # TODO MP AI hallucination?
    public_contact_emails: List[str]
    resource_organisation: str
    resource_type: str
    scientific_domains: List[str]
    slug: str
    status: str
    synchronized_at: Optional[datetime]
    tag_list: List[str]
    tagline: str
    updated_at: datetime
    upstream_id: int
    url: AnyHttpUrl
    urls: List[str]  # TODO MP AI hallucination?
    version: str
