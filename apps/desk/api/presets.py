"""This module defines the API routes for managing desk presets."""

from fastapi import APIRouter, HTTPException

from apps.desk.models.presets import (
    Preset,
    Presets,
    PresetHeightUpdateRequest,
    PresetHeightUpdateResponse,
)
from apps.desk.services.desk import DeskService
from apps.desk.dependencies import get_desk_service
from fastapi import APIRouter, HTTPException, Depends

router = APIRouter(prefix="/presets", tags=["presets"])


@router.get("/", response_model=Presets)
async def list_presets(desk_service: DeskService = Depends(get_desk_service)):
    """return all presets"""
    return desk_service.presets


@router.get("/{preset_name}", response_model=Preset)
async def get_preset(
    preset_name: str, desk_service: DeskService = Depends(get_desk_service)
):
    """Get a specific preset by name."""
    preset = desk_service.presets.root.get(preset_name)
    if not preset:
        raise HTTPException(status_code=404, detail="Preset not found")
    return preset


@router.put("/{preset_name}", response_model=PresetHeightUpdateResponse)
async def update_preset(
    preset_name: str,
    preset_data: PresetHeightUpdateRequest,
    desk_service: DeskService = Depends(get_desk_service),
):
    """Update a specific preset by name."""
    try:
        desk_service.update_preset_height(preset_name, preset_data.height)
        return PresetHeightUpdateResponse(success=True, height=preset_data.height)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/", response_model=Preset)
async def create_preset(
    preset_data: Preset, desk_service: DeskService = Depends(get_desk_service)
):
    """Create a new preset."""
    try:
        desk_service.add_preset(preset_data)
        return preset_data
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{preset_name}")
async def delete_preset(
    preset_name: str, desk_service: DeskService = Depends(get_desk_service)
):
    """Delete a specific preset by name."""
    try:
        desk_service.remove_preset(preset_name)
        return {"detail": "Preset deleted"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
