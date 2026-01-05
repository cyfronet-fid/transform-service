from typing import Literal

from pydantic import BaseModel, Field


class EgaOutput(BaseModel):
    id: str = Field(..., description="The dataset accession ID")
    title: str = Field(..., description="The dataset title")
    description: str = Field(..., description="The dataset description")
    type: Literal["dataset"] = "dataset"
    datasource_pids: list[str] = Field(default_factory=lambda: ["eosc.ega.ega"])
    best_access_right: str = Field(..., description="The dataset access type")
    publication_date: str | None = Field(None, description="The dataset released date")
    node: str = "EOSC PL"
    dataset_types: list[str] = Field(..., description="The dataset types")
    technologies: list[str] | None = Field(None, description="The dataset technologies")
    num_samples: int = Field(..., ge=0, description="The dataset number of samples")
    is_in_beacon: bool = Field(..., description="The dataset is in beacon")
    is_released: bool = Field(..., description="The dataset released flag")
    is_deprecated: bool = Field(..., description="The dataset deprecated flag")
    policy_accession_id: str | None = Field(
        None, description="The dataset's policy's accession ID"
    )
    url: list[str] = Field(..., description="The URL of the dataset")
