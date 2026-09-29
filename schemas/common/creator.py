"""Creator model schema."""

from pydantic import AnyHttpUrl, BaseModel, EmailStr


class CreatorNameTypeInfo(BaseModel):
    """
    Additional information describing the creator's preferred display name.

    Attributes:
        nameType (str | None):
            Type of the creator's name (e.g. "Organizational" or "Personal").
            Optional because some data sources do not provide it.
        creatorName (str | None):
            Preferred full display name of the creator.
            Optional because some data sources only provide first and last names.
    """

    nameType: str | None = None
    creatorName: str | None = None


class CreatorAffiliationInfo(BaseModel):
    """
    Additional information describing the creator's affiliation.

    Attributes:
        affiliation (str | None):
            Name of the creator's affiliated organisation.
        affiliationIdentifier (AnyHttpUrl | None):
            Persistent identifier of the affiliation (e.g. a ROR identifier).
    """

    affiliation: str | None = None
    affiliationIdentifier: AnyHttpUrl | None = None


class Creator(BaseModel):
    """
    Model representing a creator of a deployable service.

    Attributes:
        firstName (str):
            Creator's given (first) name.
        lastName (str):
            Creator's family (last) name.
        email (EmailStr | None):
            Public email address of the creator, when available.
        role (str | None):
            Creator's contribution role (e.g. CRediT taxonomy).
        nameIdentifier (AnyHttpUrl | None):
            Persistent identifier of the creator (e.g. ORCID or GitHub profile).
        creatorNameTypeInfo (CreatorNameTypeInfo | None):
            Optional metadata describing the creator's name. Currently empty.
        creatorAffiliationInfo (CreatorAffiliationInfo | None):
            Optional metadata describing the creator's organisational affiliation. Currently empty.
    """

    firstName: str
    lastName: str
    email: EmailStr | None = None
    role: str | None = None
    nameIdentifier: AnyHttpUrl | None = None
    creatorNameTypeInfo: CreatorNameTypeInfo | None = None
    creatorAffiliationInfo: CreatorAffiliationInfo | None = None
