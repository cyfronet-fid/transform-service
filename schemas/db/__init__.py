from schemas.db.bundle import BundleDBSchema
from schemas.db.catalogue import CatalogueDBSchema
from schemas.db.data_source import DataSourceDBSchema
from schemas.db.dataset import DatasetDBSchema
from schemas.db.guideline import GuidelineDBSchema
from schemas.db.offer import OfferDBSchema
from schemas.db.organisation import OrganisationDBSchema
from schemas.db.other_rp import OtherRPDBSchema
from schemas.db.project import ProjectDBSchema
from schemas.db.provider import ProviderDBSchema
from schemas.db.publication import PublicationDBSchema
from schemas.db.service import ServiceDBSchema
from schemas.db.software import SoftwareDBSchema
from schemas.db.training import TrainingDBSchema

"""Expected schemas for database"""

__all__ = [
    "CatalogueDBSchema",
    "BundleDBSchema",
    "DataSourceDBSchema",
    "DatasetDBSchema",
    "GuidelineDBSchema",
    "OfferDBSchema",
    "OrganisationDBSchema",
    "OtherRPDBSchema",
    "ProjectDBSchema",
    "ProviderDBSchema",
    "PublicationDBSchema",
    "ServiceDBSchema",
    "SoftwareDBSchema",
    "TrainingDBSchema",
]
