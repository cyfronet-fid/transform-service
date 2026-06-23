"""Data source expected search engine schema"""

from datetime import date, datetime
from typing import List, Optional

from pydantic import AnyHttpUrl, BaseModel, EmailStr


class DataSourceSESchema(BaseModel):
    """
    Pydantic model representing a search engine document schema for a data source.

    Attributes:
        access_policies_url (Optional[str]):
            URL describing access policies for the data source.
        access_types (Optional[List[str]]):
            List of access types available for the data source.
        best_access_right (Optional[str]):
            Highest level of access rights available for the data source.
        catalogue (Optional[str]):
            Primary catalogue associated with the data source.
        catalogues (Optional[List[st`r]]):
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
        keywords (Optional[List[str]]):
            Keywords associated with the data source.
        keywords_tg (Optional[List[str]]):
            Search-optimized representation of keywords.
        logo (Optional[str]):
            URL or path to the data source logo.
        node (str):
            Name of the node associated with the data source.
        open_access (Optional[bool]):
            Indicates whether the data source is openly accessible.
        order_url (Optional[str]):
            URL used to order or request access to the data source.
        pid (str):
            Persistent identifier of the data source.
        popularity (Optional[int]):
            Popularity score calculated for ranking and sorting purposes.
        privacy_policy_url (Optional[str]):
            URL to the privacy policy.
        providers (Optional[List[str]]):
            Organizations or entities providing the data source.
        public_contacts (Optional[List[str]]):
            Public contact information associated with the data source.
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
        tag_list_tg (Optional[List[str]]):
            Search-optimized representation of tags.
        terms_of_use_url (Optional[str]):
            URL to the terms of use.
        title (Optional[str]):
            Title of the data source used for indexing and searching.
        thematic (Optional[bool]):
            Indicates whether the data source is thematic.
        trl (Optional[str]):
            Technology Readiness Level associated with the data source.
        type (Optional[str]):
            Resource type identifier.
        updated_at (Optional[datetime]):
            Timestamp of the last update.
        upstream_id (Optional[int]):
            Identifier of the source record in the upstream system.
        url (Optional[List[str]]):
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
    best_access_right: Optional[str] = None
    catalogue: Optional[str] = None
    catalogues: Optional[List[str]] = None
    categories: Optional[List[str]] = None
    created_at: Optional[datetime] = None
    datasource_classification: Optional[str] = None
    description: Optional[str] = None
    guidelines: Optional[list[str]] = None
    id: int
    jurisdiction: Optional[str] = None
    keywords: Optional[List[str]] = None
    keywords_tg: Optional[List[str]] = None
    logo: Optional[str] = None
    node: str
    open_access: Optional[bool] = None
    order_url: Optional[str] = None
    pid: str
    popularity: Optional[int] = None
    privacy_policy_url: Optional[str] = None
    providers: Optional[List[str]] = None
    public_contacts: Optional[List[str]] = None
    publication_date: Optional[datetime] = None
    research_product_types: Optional[List[str]] = None
    resource_organisation: Optional[str] = None
    scientific_domains: Optional[List[str]] = None
    status: Optional[str] = None
    synchronized_at: Optional[datetime] = None
    tag_list: Optional[List[str]] = None
    tag_list_tg: Optional[List[str]] = None
    terms_of_use_url: Optional[str] = None
    title: Optional[str] = None
    thematic: Optional[bool] = None
    trl: Optional[str]
    type: Optional[str] = None
    updated_at: Optional[datetime] = None
    upstream_id: Optional[int] = None
    url: Optional[List[str]] = None  #
    usage_counts_downloads: Optional[int] = None
    usage_counts_views: Optional[int] = None
    version_control: Optional[bool] = None
    webpage_url: Optional[str] = None
