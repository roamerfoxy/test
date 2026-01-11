"""This module provides the business logic for controlling the desk."""

import asyncio
import json
import os
from apps.desk.core.config import settings
from apps.desk.drivers.desk_driver import DeskDriver
from apps.desk.models.desk import DeskState
from apps.desk.models.presets import Preset, Presets
from apps.desk.core.logger import get_logger

logger = get_logger(__name__)


class DeskService:
    """
    Service for controlling a desk using a BLE-connected desk driver.

    This class provides methods to get and set the desk height,
    move the desk to preset positions, and manage the desk's connection
    and state.

    Attributes:
        driver (DeskDriver): The BLE driver for communicating with the desk.

    Methods:
        get_height(): Returns the current height of the desk.
        set_height(height: int): Sets the target height of the desk,
            initiating an asynchronous movement.
        set_preset(preset_name: str): Moves the desk to a preset height.
    """

    def __init__(self):
        self.driver = DeskDriver(settings.mac_address)
        self.state = DeskState(
            name="my_desk",
            current_height=1200,
            target_height=1300,
            is_moving=False,
            active_preset=None,
        )
        self.presets_file = settings.presets_file
        self.presets = self.load_presets()

    def load_presets(self) -> Presets:
        if os.path.exists(self.presets_file):
            try:
                with open(self.presets_file, "r") as f:
                    data = json.load(f)
                    # Convert dict to Presets model, ensuring correct types
                    # Assumes JSON structure matches what Pydantic expects (dict of Presets)
                    # We might need to map it if the JSON is just the root dict
                    return Presets(root={k: Preset(**v) for k, v in data.items()})
            except Exception as e:
                logger.error(f"Error loading presets: {e}")

        # Defaults
        return Presets(
            root={
                "Standing": Preset(name="Standing", height=1050),
                "Sitting": Preset(name="Sitting", height=680),
            }
        )

    def save_presets(self):
        try:
            os.makedirs(os.path.dirname(self.presets_file), exist_ok=True)
            with open(self.presets_file, "w") as f:
                # Dump the root dict
                f.write(
                    json.dumps(
                        {k: v.model_dump() for k, v in self.presets.root.items()},
                        indent=4,
                    )
                )
        except Exception as e:
            logger.error(f"Error saving presets: {e}")

    def add_preset(self, preset: Preset):
        if preset.name in self.presets.root:
            raise ValueError("Preset already exists")
        self.presets.root[preset.name] = preset
        self.save_presets()

    def remove_preset(self, name: str):
        if name not in self.presets.root:
            raise ValueError("Preset not found")
        del self.presets.root[name]
        self.save_presets()

    def update_preset_height(self, name: str, height: int):
        if name not in self.presets.root:
            raise ValueError("Preset not found")
        self.presets.root[name].height = height
        self.save_presets()

    def _update_state(self, height: int, speed: int):
        self.state.current_height = height
        self.state.is_moving = speed != 0

    def get_height(self) -> int:
        """Returns the current height of the desk."""
        return self.state.current_height

    def set_height(self, height: int):
        """Sets the target height of the desk and starts moving asynchronously."""
        logger.info(f"Setting desk height to {height}mm")
        asyncio.create_task(self._async_set_height(height))
        self.state.target_height = height

    async def _async_set_height(self, height: int):
        try:
            await self.driver.connect()
            await self.driver.subscribe(callback=self._update_state)
            await self.driver.wake_up()
            await self.driver.stop()
            stationary_count = 0
            while True:
                await self.driver.move_to_height(height)
                await asyncio.sleep(0.1)

                # Success case: Target reached (within tolerance, usually handled by desk/firmware)
                if self.state.current_height == height:
                    logger.info(f"Target height {height} reached.")
                    break

                # Safety/Obstruction case: Desk stopped moving unexpectedly
                if not self.state.is_moving:
                    stationary_count += 1
                    # 0.1s sleep * 50 = 5 seconds
                    if stationary_count >= 50:
                        logger.warning(
                            "Desk stopped moving for 5s (Obstruction detected or limit reached)."
                        )
                        break
                else:
                    stationary_count = 0
        except Exception as e:
            logger.error(f"Error setting desk height to {height}: {e}")
            raise
        finally:
            await self.driver.unsubscribe()
            await self.driver.stop()
            await self.driver.disconnect()

    def set_preset(self, preset_name: str):
        """Moves the desk to a preset height."""
        if preset_name in self.presets.root:
            height = self.presets.root[preset_name].height
            logger.info(f"Applying preset '{preset_name}' with height {height}mm")
            self.set_height(height)
            self.state.active_preset = preset_name
        else:
            logger.warning(f"Preset '{preset_name}' not found")
