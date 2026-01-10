"""This module defines the API routes for controlling the desk."""

from fastapi import APIRouter, HTTPException

from apps.desk.models.desk import DeskState, HeightUpdateRequest, HeightUpdateResponse
from apps.desk.models.presets import PresetApplyRequest, PresetApplyResponse
from apps.desk.core.state import desk_state, presets

from apps.desk.services.desk import DeskService

router = APIRouter(prefix="/desk", tags=["desk"])
desk_service = DeskService()


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "desk_connected": desk_service.driver.client is not None
        and desk_service.driver.client.is_connected,
    }


@router.get("/", response_model=DeskState)
async def get_desk_state():
    """Returns the current state of the desk."""
    return desk_state


@router.put("/height", response_model=HeightUpdateResponse)
async def update_desk_height(height_update: HeightUpdateRequest):
    """Updates the target height of the desk."""
    desk_service.set_height(height_update.height)
    return HeightUpdateResponse(success=True, height=desk_state.current_height)


@router.put("/preset", response_model=PresetApplyResponse)
async def apply_preset(preset_apply: PresetApplyRequest):
    """Applies a preset to the desk."""
    if preset_apply.name not in presets.root:
        raise HTTPException(status_code=404, detail="Preset not found")
    desk_service.set_preset(preset_apply.name)
    return PresetApplyResponse(success=True, height=desk_state.current_height)
