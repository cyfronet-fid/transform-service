"""Creator model schema"""

from pydantic import AnyHttpUrl, BaseModel


class CreatorNameTypeInfo(BaseModel):
    """
    Information about the creator's name type.

    Attributes:
        nameType (str):
            The type of the creator's name (e.g., "ir_name_type-organizational").
        creatorName (str):
            The full name of the creator.
    """

    nameType: str
    creatorName: str


class CreatorAffiliationInfo(BaseModel):
    """
    Information about the creator's affiliation.

    Attributes:
        affiliation (str):
            The name of the organization the creator is affiliated with.
        affiliationIdentifier (AnyHttpUrl):
            The identifier URL for the affiliation (e.g., ROR ID).
    """

    affiliation: str
    affiliationIdentifier: AnyHttpUrl


class Creator(BaseModel):
    """
    Model representing a creator/author of a deployable service.

    Attributes:
        givenName (str):
            The given (first) name of the creator.
        familyName (str):
            The family (last) name of the creator.
        nameIdentifier (AnyHttpUrl):
            The identifier URL for the creator (e.g., GitHub profile, ORCID).
        creatorNameTypeInfo (CreatorNameTypeInfo):
            Information about the creator's name type.
        creatorAffiliationInfo (CreatorAffiliationInfo):
            Information about the creator's organizational affiliation.
    """

    givenName: str
    familyName: str
    nameIdentifier: AnyHttpUrl
    creatorNameTypeInfo: CreatorNameTypeInfo
    creatorAffiliationInfo: CreatorAffiliationInfo
