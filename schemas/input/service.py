"""Service expected input schema"""

from datetime import date, datetime
from typing import List, Optional, Union

from pydantic import BaseModel


class ServiceInputSchema(BaseModel):
    """
    Schema representing a service available in the EOSC ecosystem.

    Attributes:
        access_policies_url (Optional[str]):
            URL describing access and usage policies.
        access_types (Optional[List[str]]):
            Available access methods or access conditions.
        categories (Optional[List[str]]):
            Classification categories assigned to the service.
        created_at (Optional[datetime]):
            Timestamp when the service record was created.
        description (str):
            Detailed description of the service, including its purpose and functionality.
        guidelines (Optional[List[str]]):
            Documentation, guides, or best practices related to the service.
        id (int):
            Internal unique identifier of the service.
        jurisdiction (Optional[str]):
            Legal or geographical jurisdiction under which the service operates.
        logo (Optional[str]):
            URL of the service logo or graphical representation.
        name (str):
            Official name of the service.
        nodes (List[str]):
            EOSC nodes or infrastructures associated with the service.
        offers_count (Optional[int]):
            Number of offers associated with the service.
        order_type (str):
            Method used to request or obtain access to the service.
        order_url (Optional[str]):
            URL for ordering, requesting, or accessing the service.
        pid (str):
            Persistent identifier assigned to the service.
        ppid (Optional[str]):
            Parent persistent identifier, if applicable.
        privacy_policy_url (Optional[str]):
            URL to the privacy policy.
        providers (Optional[List[str]]):
            Organisations providing the service.
        public_contact_emails (List[str]):
            Public contact email addresses for support or inquiries.
        publication_date (datetime):
            Official publication date of the service.
        publishing_date (Optional[str]):
            Publication date provided by the source system.
        rating (str):
            Overall service rating or evaluation score.
        resource_organisation (str):
            Organisation responsible for operating or maintaining the service.
        resource_type (Optional[str]):
            Type of resource represented by the service.
        scientific_domains (Optional[List[str]]):
            Scientific disciplines or research domains supported by the service.
        service_opinion_count (Optional[int]):
            Number of user opinions or reviews.
        slug (str):
            Human-readable unique identifier used in URLs.
        status (str):
            Current operational or publication status of the service.
        synchronized_at (Optional[datetime]):
            Timestamp of the last synchronization with the source system.
        tag_list (Optional[List[str]]):
            Keywords describing the service and its capabilities.
        terms_of_use_url (Optional[str]):
            URL to the service terms and conditions.
        trls (Optional[str]):
            Technology Readiness Level (TRL) information.
        updated_at (Optional[datetime]):
            Timestamp of the most recent update of the service record.
        upstream_id (Optional[int]):
            Identifier of the source record in an external system.
        urls (Optional[List[str]]):
            Additional URLs related to the service.
        usage_counts_downloads (Optional[int]):
            Total number of service downloads.
        usage_counts_views (Optional[int]):
            Total number of service page views.
        webpage_url (str):
            URL of the main service webpage.
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
