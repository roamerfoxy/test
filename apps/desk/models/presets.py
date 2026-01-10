"""This module defines the data models for desk presets."""

from pydantic import BaseModel, RootModel, Field
from apps.desk.core.config import settings


class Preset(BaseModel):
    """Represents a desk height preset."""

    name: str
    height: int = Field(
        ...,
        gt=settings.min_height,
        lt=settings.max_height,
        description="Height in millimeters",
    )


class Presets(RootModel[dict[str, Preset]]):
    """Represents a collection of desk height presets."""


class PresetApplyRequest(BaseModel):
    """Represents a request to apply a desk height preset."""

    name: str


class PresetApplyResponse(BaseModel):
    """Represents a response to a request to apply a desk height preset."""

    success: bool
    height: int


class PresetHeightUpdateRequest(BaseModel):
    """Represents a request to update the height of a desk height preset."""

    height: int = Field(..., gt=settings.min_height, lt=settings.max_height)


class PresetHeightUpdateResponse(BaseModel):
    """Represents a response to a request to update the height of a desk height preset."""

    success: bool
    height: int
