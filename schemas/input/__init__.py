"""Expected schemas for input data"""

"""Import input schemas"""

from .bundle import BundleInputSchema
from .catalogue import CatalogueInputSchema
from .data_source import DataSourceInputSchema
from .dataset import DatasetInputSchema
from .guideline import GuidelineInputSchema
from .offer import OfferInputSchema
from .organisation import OrganisationInputSchema
from .other_rp import OtherRPInputSchema
from .project import ProjectInputSchema
from .provider import ProviderInputSchema
from .publication import PublicationInputSchema
from .service import ServiceInputSchema
from .software import SoftwareInputSchema
from .training import TrainingInputSchema

__all__ = [
    "CatalogueInputSchema",
    "BundleInputSchema",
    "DataSourceInputSchema",
    "DatasetInputSchema",
    "GuidelineInputSchema",
    "OfferInputSchema",
    "OrganisationInputSchema",
    "OtherRPInputSchema",
    "ProjectInputSchema",
    "ProviderInputSchema",
    "PublicationInputSchema",
    "ServiceInputSchema",
    "SoftwareInputSchema",
    "TrainingInputSchema",
]
