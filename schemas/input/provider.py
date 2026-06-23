"""Provider expected input schema"""

from datetime import datetime
from typing import List, Optional

from pydantic import AnyHttpUrl, BaseModel

from schemas.common.public_contact import PublicContact
from schemas.common.url import BasicURL


class MultimediaUrl(BaseModel):
    name: str
    url: str


class ProviderInputSchema(BaseModel):
    """
    Pydantic model representing the expected input schema for a provider.

    Attributes:
        abbreviation (str):
            The abbreviation of the provider.
        catalogues (Optional[List[str]]):
            A list of catalogues associated with the provider.
        country (str):
            The country where the provider is based.
        description (str):
            A detailed description of the provider.
        hosting_legal_entity (Optional[str]):
            The legal entity hosting the provider.
        id (int):
            The unique identifier of the provider.
        legal_entity (Optional[bool]):
            Indicates whether the provider is a legal entity.
        legal_status (Optional[str]):
            The legal status of the provider.
        multimedia_urls (Optional[List[MultimediaUrl]]):
            A list of multimedia resources related to the provider.
        name (str):
            The name of the provider.
        node (Optional[str]):
            Name of the node associated with the provider.
        pid (str):
            The persistent identifier of the provider.
        public_contact_emails (List[str]):
            A list of public contact email addresses for the provider.
        publication_date (datetime):
            The date when the provider was published.
        slug (str):
            URL-friendly identifier of the provider.
        updated_at (datetime):
            The date and time when the provider record was last updated.
        usage_counts_downloads (Optional[int]):
            The number of times the provider's resources have been downloaded.
        usage_counts_views (Optional[int]):
            The number of times the provider's resources have been viewed.
        webpage_url (AnyHttpUrl):
            The primary webpage URL of the provider.
    """

    abbreviation: str
    catalogues: Optional[List[str]]
    country: str
    description: str
    hosting_legal_entity: Optional[str]
    id: int
    legal_entity: Optional[bool]
    legal_status: Optional[str]
    multimedia_urls: Optional[List[MultimediaUrl]]
    name: str
    node: Optional[str]
    pid: str
    public_contact_emails: List[str]
    publication_date: datetime
    slug: str
    updated_at: datetime
    usage_counts_downloads: Optional[int]
    usage_counts_views: Optional[int]
    webpage_url: AnyHttpUrl
