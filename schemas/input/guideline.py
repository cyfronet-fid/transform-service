"""Interoperability Guideline expected input schema"""

from datetime import date
from typing import List, Optional

from pydantic import BaseModel


class AlternativePID(BaseModel):
    """Alternative persistent identifier metadata."""

    pid: Optional[str] = None
    pidSchema: Optional[str] = None


class RelatedStandard(BaseModel):
    """Standard related to an interoperability guideline."""

    relatedStandardIdentifier: Optional[str] = None
    relatedStandardURI: Optional[str] = None


class ResourceTypeInfo(BaseModel):
    """Provider Component resource type metadata."""

    resourceType: Optional[str] = None
    resourceTypeGeneral: Optional[str] = None


class License(BaseModel):
    """Guideline license metadata."""

    licenseName: Optional[str] = None
    licenseURL: Optional[str] = None


class CreatorPID(BaseModel):
    """Creator persistent identifier metadata."""

    creatorPID: Optional[str] = None
    creatorPIDScheme: Optional[str] = None


class AffiliationIdentifier(BaseModel):
    """Identifier metadata for a creator affiliation."""

    creatorID: Optional[str] = None
    creatorType: Optional[str] = None


class CreatorAffiliation(BaseModel):
    """Creator affiliation metadata."""

    affiliationName: Optional[str] = None
    affiliationIdentifier: Optional[AffiliationIdentifier] = None


class Creator(BaseModel):
    """Creator metadata from Provider Component."""

    firstName: Optional[str] = None
    lastName: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    PIDs: Optional[List[CreatorPID]] = None
    affiliations: Optional[List[CreatorAffiliation]] = None


class GuidelineInputSchema(BaseModel):
    """
    Pydantic model representing the expected input schema for an interoperability guideline.

    Attributes:
        alternativePIDs (Optional[List[AlternativePID]]):
            Alternative persistent identifiers associated with the guideline.
        creators (Optional[List[Creator]]):
            List of creators responsible for the guideline.
        description (Optional[str]):
            Detailed description of the guideline.
        id (str):
            Unique identifier of the guideline.
        license (Optional[License]):
            License information associated with the guideline.
        name (str):
            Name of the guideline.
        nodePID (Optional[str]):
            Persistent identifier of the associated node.
        publicContacts (Optional[List[str]]):
            Public contact information for the guideline.
        publishingDate (Optional[date]):
            Date when the guideline was published.
        relatedStandards (Optional[List[RelatedStandard]]):
            Standards related to the guideline.
        resourceOwner (Optional[str]):
            Organization or entity responsible for the guideline.
        resourceTypeInfo (Optional[ResourceTypeInfo]):
            Resource type metadata for the guideline.
        type (Optional[str]):
            Type or category of the guideline.
        urls (Optional[List[str]]):
            URLs associated with the guideline.
    """

    alternativePIDs: Optional[List[AlternativePID]] = None
    creators: Optional[List[Creator]] = None
    description: Optional[str] = None
    id: str
    license: Optional[License] = None
    name: str
    nodePID: Optional[str] = None
    publicContacts: Optional[List[str]] = None
    publishingDate: Optional[date] = None
    relatedStandards: Optional[List[RelatedStandard]] = None
    resourceOwner: Optional[str] = None
    resourceTypeInfo: Optional[ResourceTypeInfo] = None
    type: Optional[str] = None
    urls: Optional[List[str]] = None
