"""This module defines the API routes for managing desk presets."""

from fastapi import APIRouter, HTTPException

from apps.desk.models.presets import (
    Preset,
    Presets,
    PresetHeightUpdateRequest,
    PresetHeightUpdateResponse,
)
from apps.desk.core.state import presets

router = APIRouter(prefix="/presets", tags=["presets"])


@router.get("/", response_model=Presets)
async def list_presets():
    """return all presets"""
    return presets


@router.get("/{preset_name}", response_model=Preset)
async def get_preset(preset_name: str):
    """Get a specific preset by name."""
    preset = presets.root.get(preset_name)
    if not preset:
        raise HTTPException(status_code=404, detail="Preset not found")
    return preset


@router.put("/{preset_name}", response_model=PresetHeightUpdateResponse)
async def update_preset(preset_name: str, preset_data: PresetHeightUpdateRequest):
    """Update a specific preset by name."""
    preset = presets.root.get(preset_name)
    if not preset:
        raise HTTPException(status_code=404, detail="Preset not found")
    preset.height = preset_data.height
    return PresetHeightUpdateResponse(success=True, height=preset.height)


@router.post("/", response_model=Preset)
async def create_preset(preset_data: Preset):
    """Create a new preset."""
    if preset_data.name in presets.root:
        raise HTTPException(status_code=400, detail="Preset already exists")
    presets.root[preset_data.name] = preset_data
    return preset_data


@router.delete("/{preset_name}")
async def delete_preset(preset_name: str):
    """Delete a specific preset by name."""
    preset = presets.root.pop(preset_name, None)
    if not preset:
        raise HTTPException(status_code=404, detail="Preset not found")
    return {"detail": "Preset deleted"}
