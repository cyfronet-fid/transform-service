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
        creator_affiliations (List[str]):
            A list of creator affiliations extracted from the creators field.
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
            The software license under which the deployable service is distributed.
        node (str):
            Name of the node associated with the deployable service.
        pid (str):
            Persistent identifier for the deployable service.
        publication_date (datetime):
            The date when the deployable service was published.
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
    creator_affiliations: List[str]
    creator_identifiers: List[str]
    creator_names: List[str]
    creators_searchable: List[str]
    description: str
    id: str
    keywords: List[str]
    last_update: Optional[datetime]
    license: str
    node: str
    pid: str
    publication_date: datetime
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

    """
    Transformations necessary to convert DeployableServiceInputSchema to DeployableServiceDBSchema:
        - add type = "deployable service"
        - add creator_names, creator_identifiers, creator_affiliations, creators_searchable from creators
        - rename name to title
        - rename tag_list to keywords
        - rename software_license to license
        - rename catalogue to catalogues (and convert to array)
        - cast:
            .withColumn("publication_date", col("publication_date").cast("date"))
            .withColumn("last_update", col("last_update").cast("date"))
            .withColumn("synchronized_at", col("synchronized_at").cast("date"))
            .withColumn("updated_at", col("updated_at").cast("date"))
            .withColumn("id", col("id").cast(StringType()))
            .withColumn("upstream_id", col("upstream_id").cast("bigint"))
    """
