"""Provider expected search engine schema"""

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel


class ProviderSESchema(BaseModel):
    """
    Pydantic model representing the expected search engine schema for a provider after transformations.

    Attributes:
        abbreviation (str):
            The abbreviation of the provider. Used in resource view.
        catalogue (Optional[str]):
            The primary catalogue associated with the provider.
        catalogues (Optional[List[str]]):
            A list of catalogues associated with the provider.
        country (str):
            The country where the provider is located or operates. Used in filters and resource view.
        description (str):
            A detailed description of the provider. Used in searching.
        hosting_legal_entity (Optional[str]):
            The name of the legal entity hosting the provider.
        id (int):
            Unique identifier for the provider.
        legal_entity (Optional[bool]):
            Indicates whether the provider is a legal entity.
        legal_status (Optional[str]):
            The legal status of the provider. Used in filters and tags.
        multimedia_urls (List[str]):
            A list of URLs pointing to multimedia resources related to the provider.
        node (Optional[str]):
            Name of the node associated with the provider. Used in filters.
        pid (str):
            Persistent identifier for the provider. Used in resource view.
        popularity (int):
            Popularity score of the provider. Used in sorting.
        publication_date (datetime):
            The date when the provider's information was published. Used in sorting.
        slug (str):
            URL-friendly identifier of the provider.
        title (str):
            The title of the provider. Used in searching and resource view.
        type (str):
            Data type = "provider". Used in routing and resource view.
        updated_at (datetime):
            The date and time when the provider record was last updated.
        usage_counts_downloads (int):
            The number of times the provider's resources have been downloaded. Part of popularity.
        usage_counts_views (int):
            The number of times the provider's resources have been viewed. Part of popularity.
        webpage_url (str):
            The primary webpage URL of the provider. Used in resource view and navigation.
    """

    abbreviation: str
    catalogue: Optional[str]
    catalogues: Optional[List[str]]
    country: str
    description: str
    hosting_legal_entity: Optional[str]
    id: int
    legal_entity: Optional[bool]
    legal_status: Optional[str]
    multimedia_urls: List[str]
    node: Optional[str]
    pid: str
    popularity: int
    publication_date: datetime
    slug: str
    title: str
    type: str
    updated_at: datetime
    usage_counts_downloads: int
    usage_counts_views: int
    webpage_url: str
