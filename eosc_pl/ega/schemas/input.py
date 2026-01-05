from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class EgaInput(BaseModel):
    accession_id: str = Field(..., description="The dataset accession ID")
    title: str = Field(..., description="The dataset title")
    description: Optional[str] = Field(None, description="The dataset description")
    dataset_types: list[str] = Field(..., description="The dataset types")
    technologies: Optional[list[str]] = Field(
        ..., description="The dataset technologies"
    )
    num_samples: int = Field(..., ge=0, description="The dataset number of samples")
    access_type: str = Field(..., description="The dataset access type")
    is_in_beacon: bool = Field(..., description="The dataset is in beacon")
    is_released: bool = Field(..., description="The dataset released flag")
    released_date: Optional[datetime] = Field(
        None, description="The dataset released date"
    )
    is_deprecated: bool = Field(..., description="The dataset deprecated flag")
    policy_accession_id: Optional[str] = Field(
        None, description="The dataset's policy's accession ID"
    )
