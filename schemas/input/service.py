"""Service expected input schema"""

from datetime import date, datetime
from typing import List, Optional, Union

from pydantic import BaseModel


class ServiceInputSchema(BaseModel):
    """
    Schema representing a service registered in the EOSC ecosystem.

    The model contains metadata describing a service, including its
    identification, publication details, access conditions, providers,
    scientific domains, usage statistics, and related URLs.

    Attributes:
        id: Internal unique identifier of the service.
        pid: Persistent identifier assigned to the service.
        ppid: Parent persistent identifier, if applicable.
        name: Official service name.
        slug: Human-readable identifier used in URLs.
        description: Detailed description of the service.
        status: Current service status.
        rating: Service rating or evaluation score.

        publication_date: Official publication date.
        publishing_date: Publication date provided by the source system.
        created_at: Timestamp when the service record was created.
        updated_at: Timestamp of the most recent update.
        synchronized_at: Timestamp of the last synchronization.
        upstream_id: Identifier of the source record in an external system.

        resource_type: Type of resource represented by the service.
        resource_organisation: Organisation responsible for the service.
        providers: Organisations providing the service.
        nodes: EOSC nodes or infrastructures associated with the service.

        categories: Classification categories assigned to the service.
        scientific_domains: Scientific domains supported by the service.
        tag_list: Keywords describing the service.
        guidelines: Documentation, guides, or best practices.

        access_types: Available access methods or conditions.
        access_policies_url: URL to access and usage policies.
        order_type: Method used to request or obtain access.
        order_url: URL for ordering or requesting the service.

        jurisdiction: Legal or geographical jurisdiction.
        privacy_policy_url: URL to the privacy policy.
        terms_of_use_url: URL to the terms of use.

        webpage_url: URL of the main service webpage.
        urls: Additional URLs related to the service.
        logo: URL of the service logo.

        public_contact_emails: Public contact email addresses.
        offers_count: Number of associated offers.
        service_opinion_count: Number of user opinions or reviews.
        usage_counts_downloads: Total number of downloads.
        usage_counts_views: Total number of page views.

        trls: Technology Readiness Level (TRL) information.
    """

    access_policies_url: Optional[str] = None
    access_types: Optional[List[str]] = None
    categories: Optional[List[str]] = None
    created_at: Optional[datetime] = None
    description: str
    guidelines: Optional[List[str]] = None
    id: int
    jurisdiction: Optional[str] = None
    logo: Optional[str] = None
    name: str
    nodes: List[str]
    offers_count: Optional[int] = None
    order_type: str
    order_url: Optional[str] = None
    pid: str
    ppid: Optional[str] = None
    privacy_policy_url: Optional[str] = None
    providers: Optional[List[str]] = None
    public_contact_emails: List[str]
    publication_date: datetime
    publishing_date: Optional[str] = None
    rating: str
    resource_organisation: str
    resource_type: Optional[str] = None
    scientific_domains: Optional[List[str]] = None
    service_opinion_count: Optional[int] = None
    slug: str
    status: str
    synchronized_at: Optional[datetime] = None
    tag_list: Optional[List[str]] = None
    terms_of_use_url: Optional[str] = None
    trls: Optional[str] = None
    updated_at: Optional[datetime] = None
    upstream_id: Optional[int] = None
    urls: Optional[List[str]] = None
    usage_counts_downloads: Optional[int] = None
    usage_counts_views: Optional[int] = None
    webpage_url: str
