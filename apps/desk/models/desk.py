"""This module defines the data models for the desk application."""

from typing import Optional
from pydantic import BaseModel, Field
from apps.desk.core.config import settings


class DeskState(BaseModel):
    """Represents the state of a desk."""

    name: str = "my_desk"
    current_height: int = Field(..., gt=settings.min_height, lt=settings.max_height)
    target_height: int = Field(..., gt=settings.min_height, lt=settings.max_height)
    is_moving: bool = False
    active_preset: Optional[str] = None


class HeightUpdateRequest(BaseModel):
    """Represents a request to update the desk height."""

    height: int = Field(
        ...,
        gt=settings.min_height,
        lt=settings.max_height,
        description="The new height for the desk.",
    )


class HeightUpdateResponse(BaseModel):
    """Represents a response to a height update request."""

    success: bool
    height: int
