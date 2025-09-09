"""Deployable Service expected search engine schema"""

from datetime import date
from typing import List, Optional

from pydantic import BaseModel


class DeployableServiceSESchema(BaseModel):
    """
    Pydantic model representing the expected search engine schema for a deployable service after transformations.

    Attributes:
        catalogues (List[str]):
            A list of catalogues associated with the deployable service. Used in filters.
        creator_affiliations (List[str]):
            A list of creator affiliations. Used in filters and faceting.
        creator_names (List[str]):
            A list of creator names. Used in searching and filtering.
        creators_searchable (List[str]):
            Searchable text combining creator names and affiliations. Used in searching.
        description (str):
            A detailed description of the deployable service. Used in searching.
        id (str):
            Unique identifier for the deployable service.
        keywords (List[str]):
            A list of keywords/tags categorizing the deployable service. Used in secondary tags.
        keywords_tg (List[str]):
            The same data as 'keywords' but in solr text general type. Used in searching.
        node (Optional[str]):
            Name of the node associated with the deployable service. Used in filters.
        pid (str):
            Persistent identifier for the deployable service. Used in resource view.
        publication_date (date):
            The date when the deployable service was published. Used in sorting.
        resource_organisation (str):
            The organisation responsible for the deployable service. Used in filters.
        scientific_domains (List[str]):
            A list of scientific domains associated with the deployable service. Used in filters and tags.
        slug (str):
            The slug (URL-friendly identifier) for the deployable service.
        title (str):
            The title of the deployable service. Used in searching.
        type (str):
            Data type = "deployable service". Used in routing and resource view.
        version (str):
            The version of the deployable service. Used in resource view and filtering.
    """

    catalogues: List[str]
    creator_affiliations: List[str]
    creator_names: List[str]
    creators_searchable: List[str]
    description: str
    id: str
    keywords: List[str]
    keywords_tg: List[str]
    node: Optional[str]
    pid: str
    publication_date: date
    resource_organisation: str
    scientific_domains: List[str]
    slug: str
    title: str
    type: str
    version: str

    """
    Transformations necessary to convert DeployableServiceDBSchema to DeployableServiceSESchema:
        - delete: 
            - abbreviation (internal field)
            - creator_identifiers (sensitive URLs, keep internal)
            - last_update (not needed for search)
            - license (internal field)
            - status (internal field)
            - synchronized_at (internal field)
            - tagline (not needed for search)
            - updated_at (not needed for search)
            - upstream_id (internal field)
            - url (internal field)
        - keep keywords_tg (for text_general searching)
        - cast:
            .withColumn("publication_date", col("publication_date").cast("date"))
        - apply text_general transformations for keywords_tg
    """
