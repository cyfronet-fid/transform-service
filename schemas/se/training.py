"""Training expected search engine schema"""

from datetime import date
from typing import List, Optional

from pydantic import BaseModel


class TrainingSESchema(BaseModel):
    """
    Pydantic model representing the expected search engine schema for training after transformations.

    Attributes:
        author_names (Optional[List[str]]):
            List of training author names. Used for tagging.
        author_names_tg (Optional[List[str]]):
            Author names indexed as Solr text_general fields for full-text search.
        best_access_right (str):
            Highest available access right for the training. Used in filters.
        catalogue (str):
            Primary catalogue identifier. Deprecated; planned for removal.
        catalogues (List[str]):
            List of catalogues the training belongs to.
        content_type (Optional[List[str]]):
            List of content types associated with the training. Used for tagging.
        description (Optional[str]):
            Training description indexed for full-text search.
        duration (Optional[int]):
            Training duration. Used in filters.
        id (str):
            Unique identifier of the training resource.
        keywords (Optional[List[str]]):
            Keywords describing the training. Used for tagging.
        keywords_tg (Optional[List[str]]):
            Keywords indexed as Solr text_general fields for full-text search.
        language (List[str]):
            Languages in which the training is available. Used in filters.
        level_of_expertise (str):
            Required level of expertise. Used in filters.
        learning_outcomes (List[str]):
            List of expected learning outcomes of the training.
        license (Optional[str]):
            License under which the training is distributed. Used in filters and resource view.
        node (Optional[str]):
            Name of the associated EOSC node.
        open_access (bool):
            Indicates whether the training is openly accessible.
        publicContacts (Optional[List[str]]):
            List of public contact addresses associated with the training.
        publication_date (date):
            Publication date of the training. Used for sorting.
        qualification (Optional[List[str]]):
            Qualifications or certifications associated with the training. Used in filters.
        related_services (Optional[List[str]]):
            Identifiers of services related to the training.
        resource_owner (str):
            Organisation responsible for maintaining or owning the training resource.
        resource_type (List[str]):
            Resource type classification. Used in filters.
        scientific_domains (List[List[str]]):
            Scientific domain hierarchy associated with the training. Used in filters and tagging.
        target_group (List[str]):
            Intended audience for the training. Used in filters.
        title (str):
            Training title indexed for full-text search.
        type (str):
            Resource type identifier (typically `"training"`). Used for routing and resource rendering.
        unified_categories (List[str]):
            Unified category classification. Used in filters.
        url (Optional[str]):
            URL pointing to the training resource.
    """

    author_names: Optional[List[str]]
    author_names_tg: Optional[List[str]]
    best_access_right: str
    catalogue: Optional[str]  # TODO delete
    catalogues: Optional[List[Optional[str]]]
    content_type: Optional[List[str]]
    description: Optional[str]
    duration: Optional[int]
    id: str
    keywords: Optional[List[str]]
    keywords_tg: Optional[List[str]]
    language: List[str]
    level_of_expertise: str
    learning_outcomes: List[str]
    license: Optional[str]
    node: Optional[str]
    open_access: bool
    publicContacts: Optional[List[str]] = None
    publication_date: date
    qualification: Optional[List[str]]
    related_services: Optional[List[str]]
    resource_organisation: Optional[str] = None
    resource_owner: Optional[str] = None
    resource_type: List[str]
    scientific_domains: List[List[str]]
    target_group: List[str]
    title: str
    type: str
    unified_categories: List[str]
    url: Optional[str]
