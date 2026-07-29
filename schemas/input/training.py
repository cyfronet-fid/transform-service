"""Input training expected schema"""

from datetime import datetime
from typing import Any, List, Optional, Union

from pydantic import AnyHttpUrl, BaseModel, EmailStr


class AlternativeIdentifier(BaseModel):
    """
    Model representing an alternative identifier.

    Attributes:
        type (str):
            The type of the alternative identifier.
        value (str):
            The value of the alternative identifier.
    """

    type: str
    value: str


class AlternativePID(BaseModel):
    """Alternative persistent identifier metadata."""

    pid: Optional[str] = None
    pidSchema: Optional[str] = None


class Creator(BaseModel):
    """Model representing adapter creator contact data."""

    firstName: str
    lastName: str
    email: str
    role: Optional[str] = None
    PIDs: Optional[List[Any]] = None
    affiliations: Optional[List[Any]] = None


class License(BaseModel):
    """Guideline license metadata."""

    licenseName: Optional[str] = None
    licenseURL: Optional[str] = None


class TrainingContact(BaseModel):
    """
    Model representing a contact person.

    Attributes:
        email (EmailStr):
            The email address of the contact person.
        firstName (str):
            The first name of the contact person.
        lastName (str):
            The last name of the contact person.
        organisation (str):
            The organisation of the contact person.
        phone (str):
            The phone number of the contact person.
        position (str):
            The position of the contact person.
    """

    email: EmailStr
    firstName: str
    lastName: str
    organisation: str
    phone: str
    position: str


class ScientificDomain(BaseModel):
    """
    Model representing a scientific domain and its subdomain.

    Attributes:
        scientificDomain (str):
            The scientific domain.
        scientificSubdomain (str):
            The scientific subdomain.
    """

    scientificDomain: str
    scientificSubdomain: str


class TrainingInputSchema(BaseModel):
    """
    Pydantic model representing the expected input schema for training.

    Attributes:
        accessRights (str):
            Access rights assigned to the training resource.
        alternativePIDs (Optional[List[AlternativePID]]):
            List of alternative persistent identifiers for the training.
        catalogueId (Optional[str]):
            Identifier of the catalogue the training belongs to.
        contentResourceTypes (Optional[List[str]]):
            Types of content associated with the training resource.
        creators (Optional[List[Creator]]):
            List of creators or authors of the training.
        description (str):
            Detailed description of the training.
        duration (Optional[str]):
            Duration of the training.
        eoscRelatedServices (Optional[List[str]]):
            Identifiers of EOSC services related to the training.
        expertiseLevel (str):
            Required level of expertise for participants.
        id (str):
            Unique identifier of the training resource.
        keywords (Optional[List[str]]):
            Keywords describing the training.
        languages (List[str]):
            Languages in which the training is available.
        learningOutcomes (List[str]):
            Expected learning outcomes of the training.
        learningResourceTypes (Optional[List[str]]):
            Types of learning resources represented by the training.
        license (Optional[License]):
            License under which the training is distributed.
        name (str):
            Name (title) of the training resource.
        node (Optional[str]):
            Name of the associated EOSC node.
        publicContacts (Optional[List[str]]):
            List of public contact addresses associated with the training.
        publishingDate (str):
            Date when the training was published.
        qualifications (Optional[List[str]]):
            Qualifications or certifications associated with the training.
        resourceOwner (str):
            Organisation responsible for owning or maintaining the training.
        scientificDomains (Optional[List[ScientificDomain]]):
            Scientific domains and subdomains associated with the training.
        targetGroups (List[str]):
            Intended audience of the training.
        urls (Optional[List[str]]):
            URLs pointing to the training resource.
        versionDate (str):
            Version or last update date of the training resource.
    """

    accessRights: str
    alternativePIDs: Optional[List[AlternativePID]] = None
    catalogueId: Optional[str] = None
    contentResourceTypes: Optional[List[str]] = None
    creators: Optional[List[Creator]] = None
    description: str
    duration: Optional[str]
    eoscRelatedServices: Optional[List[str]] = None
    expertiseLevel: str
    id: str
    keywords: Optional[List[str]] = None
    languages: List[str]
    learningOutcomes: List[str]
    learningResourceTypes: Optional[List[str]] = None
    license: Optional[License] = None
    name: str
    node: Optional[str]
    publicContacts: Optional[List[str]] = None
    publishingDate: str
    qualifications: Optional[List[str]] = None
    resourceOwner: str
    scientificDomains: Optional[List[ScientificDomain]] = None
    targetGroups: List[str]
    urls: Optional[List[str]] = None
    versionDate: str
