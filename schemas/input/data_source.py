"""Data source expected input schema"""

from datetime import datetime
from typing import List, Optional, Union

from pydantic import AnyHttpUrl, BaseModel, EmailStr

from schemas.common.public_contact import PublicContact
from schemas.common.url import BasicURL


class PersistentIdentitySystem(BaseModel):
    """
    Model representing a persistent identity system.

    Attributes:
        entity_type (str):
            The type of the entity.
        entity_type_schemes (List[str]):
            The schemes associated with the entity type.
    """

    entity_type: str
    entity_type_schemes: List[str]


class DataSourceInputSchema(BaseModel):
    """
    Pydantic model representing the input schema for a data source.

    Attributes:
        access_policies_url (Optional[str]):
            URL describing access policies for the data source.
        access_types (Optional[List[str]]):
            List of access types available for the data source.
        catalogues (Optional[List[str]]):
            Catalogues in which the data source is registered.
        categories (Optional[List[str]]):
            Categories assigned to the data source.
        created_at (Optional[datetime]):
            Timestamp when the data source record was created.
        datasource_classification (Optional[str]):
            Classification of the data source.
        description (Optional[str]):
            Detailed description of the data source.
        guidelines (Optional[List[str]]):
            Guidelines related to the use or management of the data source.
        id (int):
            Unique identifier of the data source.
        jurisdiction (Optional[str]):
            Jurisdiction under which the data source operates.
        logo (Optional[str]):
            URL or path to the data source logo.
        name (str):
            Name of the data source.
        node (str):
            Name of the node associated with the data source.
        order_type (str):
            Type of ordering or access mechanism for the data source.
        order_url (Optional[str]):
            URL used to order or request access to the data source.
        pid (str):
            Persistent identifier of the data source.
        privacy_policy_url (Optional[str]):
            URL to the privacy policy.
        providers (Optional[List[str]]):
            Organizations or entities providing the data source.
        public_contact_emails (Optional[List[str]]):
            Public contact email addresses for inquiries.
        publication_date (Optional[datetime]):
            Date when the data source was published.
        research_product_types (Optional[List[str]]):
            Types of research products available through the data source.
        resource_organisation (Optional[str]):
            Organization responsible for maintaining the data source.
        scientific_domains (Optional[List[str]]):
            Scientific domains related to the data source.
        status (Optional[str]):
            Current status of the data source.
        synchronized_at (Optional[datetime]):
            Timestamp of the last synchronization.
        tag_list (Optional[List[str]]):
            Tags associated with the data source.
        terms_of_use_url (Optional[str]):
            URL to the terms of use.
        thematic (Optional[bool]):
            Indicates whether the data source is thematic.
        trls (Optional[str]):
            Technology Readiness Level(s) associated with the data source.
        updated_at (Optional[datetime]):
            Timestamp of the last update.
        upstream_id (Optional[int]):
            Identifier of the source record in the upstream system.
        urls (Optional[List[str]]):
            Additional URLs related to the data source.
        usage_counts_downloads (Optional[int]):
            Number of downloads recorded for the data source.
        usage_counts_views (Optional[int]):
            Number of views recorded for the data source.
        version_control (Optional[bool]):
            Indicates whether version control is supported.
        webpage_url (Optional[str]):
            Main webpage URL of the data source.
    """

    access_policies_url: Optional[str] = None
    access_types: Optional[List[str]] = None
    catalogues: Optional[List[str]] = None
    categories: Optional[List[str]] = None
    created_at: Optional[datetime] = None
    datasource_classification: Optional[str] = None
    description: Optional[str] = None
    guidelines: Optional[list[str]] = None
    id: int
    jurisdiction: Optional[str] = None
    logo: Optional[str] = None
    name: str
    node: str
    order_type: str
    order_url: Optional[str] = None
    pid: str
    privacy_policy_url: Optional[str] = None
    providers: Optional[List[str]] = None
    public_contact_emails: Optional[List[str]] = None
    publication_date: Optional[datetime] = None
    research_product_types: Optional[List[str]] = None
    resource_organisation: Optional[str] = None
    scientific_domains: Optional[List[str]] = None
    status: Optional[str] = None
    synchronized_at: Optional[datetime] = None
    tag_list: Optional[List[str]] = None
    terms_of_use_url: Optional[str] = None
    thematic: Optional[bool] = None
    trls: Optional[str]
    updated_at: Optional[datetime] = None
    upstream_id: Optional[int] = None
    urls: Optional[List[str]] = None
    usage_counts_downloads: Optional[int] = None
    usage_counts_views: Optional[int] = None
    version_control: Optional[bool] = None
    webpage_url: Optional[str] = None
