"""This module manages the desk's state and presets."""

from apps.desk.models.desk import DeskState
from apps.desk.models.presets import Preset, Presets

desk_state = DeskState(
    name="my_desk",
    current_height=1200,
    target_height=1300,
    is_moving=False,
    active_preset=None,
)

presets = Presets(
    root={
        "Standing": Preset(name="Standing", height=1050),
        "Sitting": Preset(name="Sitting", height=680),
    }
)
