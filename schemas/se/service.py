"""Service expected search engine schema"""

from datetime import date
from typing import List, Optional

from pydantic import BaseModel


class ServiceSESchema(BaseModel):
    """
    Search engine schema representing a transformed EOSC service document.

    Attributes:
        access_policies_url (Optional[str]):
            URL describing access and usage policies.
        access_types (Optional[List[str]]):
            Available access methods or access conditions.
        best_access_right (Optional[str]):
            Highest available access level for the service.
        categories (Optional[List[str]]):
            Classification categories used for filtering.
        description (str):
            Detailed service description used for indexing and searching.
        guidelines (Optional[List[str]]):
            Documentation, guides, or best practices related to the service.
        id (str):
            Unique identifier of the indexed service document.
        jurisdiction (Optional[str]):
            Legal or geographical jurisdiction under which the service operates.
        keywords (Optional[List[str]]):
            Keywords used for filtering and search.
        keywords_tg (Optional[List[str]]):
            Search-optimized representation of keywords.
        logo (Optional[str]):
            URL of the service logo.
        node (Optional[List[str]]):
            EOSC nodes associated with the service.
        offers_count (Optional[int]):
            Number of offers associated with the service.
        open_access (bool):
            Indicates whether the service is openly accessible.
        order_right (Optional[str]):
            Method or conditions for obtaining access to the service.
        order_url (Optional[str]):
            URL for ordering, requesting, or accessing the service.
        pid (str):
            Persistent identifier assigned to the service.
        popularity (int):
            Calculated popularity score used for sorting.
        privacy_policy_url (Optional[str]):
            URL to the privacy policy.
        providers (Optional[List[str]]):
            Organisations providing the service.
        publication_date (Optional[date]):
            Official publication date of the service.
        public_contact_emails (Optional[List[str]]):
            Public contact email addresses for support or inquiries.
        rating (str):
            Overall service rating or evaluation score.
        resource_organisation (str):
            Organisation responsible for operating or maintaining the service.
        scientific_domains (Optional[List[str]]):
            Scientific disciplines or research domains supported by the service.
        service_opinion_count (Optional[int]):
            Number of user opinions or reviews.
        slug (str):
            Human-readable unique identifier used in URLs.
        status (str):
            Current operational or publication status of the service.
        synchronized_at (Optional[date]):
            Date of the last synchronization with the source system.
        tag_list (Optional[List[str]]):
            Keywords describing the service and its capabilities.
        tag_list_tg (Optional[List[str]]):
            Search-optimized representation of tag_list.
        terms_of_use_url (Optional[str]):
            URL to the service terms and conditions.
        title (str):
            Service title used for display and full-text search.
        trl (Optional[str]):
            Technology Readiness Level (TRL) information.
        type (str):
            Resource type identifier used for routing and indexing.
        updated_at (Optional[date]):
            Date of the most recent update.
        upstream_id (Optional[int]):
            Identifier of the source record in an external system.
        url (Optional[List[str]]):
            Additional URLs related to the service.
        usage_counts_downloads (Optional[int]):
            Total number of service downloads.
        usage_counts_views (Optional[int]):
            Total number of service page views.
        webpage_url (str):
            URL of the main service webpage.
    """

    access_policies_url: Optional[str] = None
    access_types: Optional[list[str]] = None
    best_access_right: Optional[str] = None
    catalogue: str
    catalogues: list[str]
    categories: Optional[list[str]] = None
    description: str
    guidelines: Optional[list[str]] = None
    id: str
    jurisdiction: Optional[str] = None
    keywords: Optional[list[str]] = None
    keywords_tg: Optional[list[str]] = None
    logo: Optional[str] = None
    node: Optional[list[str]] = None
    offers_count: Optional[int] = None
    open_access: bool = False
    order_right: Optional[str] = None
    order_url: Optional[str] = None
    pid: str
    popularity: int = 0
    privacy_policy_url: Optional[str] = None
    providers: Optional[list[str]] = None
    publication_date: Optional[date] = None
    public_contact_emails: Optional[list[str]] = None
    rating: str
    resource_organisation: str
    scientific_domains: Optional[list[str]] = None
    service_opinion_count: Optional[int] = None
    slug: str
    status: str
    synchronized_at: Optional[date] = None
    tag_list: Optional[list[str]] = None
    tag_list_tg: Optional[list[str]] = None
    terms_of_use_url: Optional[str] = None
    title: str
    trl: Optional[str] = None
    type: str
    updated_at: Optional[date] = None
    upstream_id: Optional[int] = None
    url: Optional[list[str]] = None
    usage_counts_downloads: Optional[int] = None
    usage_counts_views: Optional[int] = None
    webpage_url: str
