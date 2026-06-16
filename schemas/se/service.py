"""Service expected search engine schema"""

from datetime import date
from typing import List, Optional

from pydantic import BaseModel


class ServiceSESchema(BaseModel):
    """
    Search Engine schema representing a transformed EOSC service document.

    The model contains fields optimized for indexing, filtering, sorting,
    and full-text search in the search engine.

    Attributes:
        id: Unique identifier of the indexed service document.
        pid: Persistent identifier of the service.
        slug: Human-readable identifier used in URLs.
        title: Service title used for display and search.
        description: Service description used for full-text search.
        type: Resource type identifier (typically ``"service"``).

        publication_date: Service publication date.
        updated_at: Date of the most recent update.
        synchronized_at: Date of the last synchronization.
        upstream_id: Identifier of the source record.

        status: Current service status.
        rating: Service rating or evaluation score.
        popularity: Calculated popularity score used for sorting.

        resource_organisation: Organisation responsible for the service.
        providers: Organisations providing the service.
        node: EOSC nodes associated with the service.

        categories: Service categories used for filtering.
        scientific_domains: Scientific domains supported by the service.
        tag_list: Tags assigned to the service.
        tag_list_tg: Search-optimized representation of ``tag_list``.
        keywords: Keywords used for filtering and search.
        keywords_tg: Search-optimized representation of ``keywords``.

        access_types: Available access methods or conditions.
        best_access_right: Highest available access level.
        access_policies_url: URL to access and usage policies.
        open_access: Indicates whether the service is openly accessible.
        order_right: Method or conditions for obtaining access.
        order_url: URL for ordering or requesting the service.

        jurisdiction: Legal or geographical jurisdiction.
        privacy_policy_url: URL to the privacy policy.
        terms_of_use_url: URL to the terms of use.

        webpage_url: Main service webpage URL.
        url: Additional service-related URLs.
        logo: URL of the service logo.

        public_contact_emails: Public contact email addresses.
        offers_count: Number of associated offers.
        service_opinion_count: Number of user opinions or reviews.
        usage_counts_downloads: Total number of downloads.
        usage_counts_views: Total number of page views.

        guidelines: Documentation, guides, or best practices.
        trl: Technology Readiness Level (TRL) information.
    """

    access_policies_url: Optional[str] = None
    access_types: Optional[list[str]] = None
    best_access_right: Optional[str] = None
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
