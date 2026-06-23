"""Guideline expected search engine schema."""

from datetime import date
from typing import List, Optional

from pydantic import BaseModel


class GuidelineSESchema(BaseModel):
    """
    Pydantic model representing a flattened interoperability guideline record
    transformed for indexing in Solr.

    Attributes:
        alternative_id_schemes (List[str]):
            Schemes corresponding to alternative identifiers.
        alternative_ids (Optional[str]):
            Alternative identifiers associated with the guideline.
        author_affiliations (List[str]):
            Names of creator affiliations.
        author_affiliations_id (List[str]):
            Identifiers of creator affiliations.
        author_family_names (List[str]):
            Family names of authors.
        author_given_names (List[str]):
            Given names of authors.
        author_names (List[str]):
            Names of authors extracted for indexing.
        author_names_id (List[str]):
            Persistent identifiers of authors.
        author_names_tg (List[str]):
            Tokenized or normalized author names used for search and aggregation.
        author_types (List[str]):
            Types of creator affiliation identifiers.
        catalogue (Optional[str]):
            Primary catalogue associated with the guideline.
        catalogues (List[str]):
            Catalogues in which the guideline is available.
        creators (str):
            JSON string representing list of author/creator objects.
        description (List[str]):
            Description of the guideline.
        id (str):
            Unique identifier of the guideline.
        license (Optional[str]):
            License name associated with the guideline.
        license_url (Optional[str]):
            URL pointing to the license information.
        node (Optional[str]):
            Name of the node associated with the guideline.
        provider (Optional[str]):
            Name of the provider associated with the guideline.
        providers (Optional[List[str]]):
            List of providers associated with the guideline.
        publication_date (Optional[date]):
            Publication date of the guideline.
        publication_year (Optional[int]):
            Publication year of the guideline.
        public_contacts (List[str]):
            Public contact information associated with the guideline.
        related_standards_id (List[str]):
            Identifiers of standards related to the guideline.
        related_standards_uri (List[str]):
            URIs of standards related to the guideline.
        resource_owner (Optional[str]):
            Organization or entity responsible for the guideline.
        title (List[str]):
            Title of the guideline.
        type (str):
            Type or category of the guideline.
        type_general (List[str]):
            General resource type classifications.
        type_info (List[str]):
            Specific resource type information.
    """

    alternative_id_schemes: List[str]
    alternative_ids: Optional[str] = None
    author_affiliations: List[str]
    author_affiliations_id: List[str]
    author_family_names: List[str]
    author_given_names: List[str]
    author_names: List[str]
    author_names_id: List[str]
    author_names_tg: List[str]
    author_types: List[str]
    catalogue: Optional[str] = None
    catalogues: List[str]
    creators: str
    description: List[str]
    id: str
    license: Optional[str] = None
    license_url: Optional[str] = None
    node: Optional[str] = None
    provider: Optional[str] = None
    providers: Optional[List[str]] = None
    publication_date: Optional[date] = None
    publication_year: Optional[int] = None
    public_contacts: List[str]
    related_standards_id: List[str]
    related_standards_uri: List[str]
    resource_owner: Optional[str] = None
    title: List[str]
    type: str
    type_general: List[str]
    type_info: List[str]
