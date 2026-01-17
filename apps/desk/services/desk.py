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
            name="desk_controller",
            current_height=1200,
            target_height=1300,
            is_moving=False,
            active_preset=None,
        )
        self.presets_file = settings.presets_file
        self.presets = self.load_presets()
        self.current_task: Optional[asyncio.Task] = None

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

        # Cancel existing task if it exists
        if self.current_task and not self.current_task.done():
            logger.info("Canceling existing movement task")
            self.current_task.cancel()

        async def move_with_retry():
            success = await self._async_set_height(height)
            if not success:
                logger.info(f"Initial attempt to set height to {height}mm failed. Retrying...")
                success = await self._async_set_height(height)
                if success:
                    logger.info(f"Retry successful. Target height {height}mm reached.")
                else:
                    logger.warning(f"Retry failed to reach target height {height}mm.")
            return success

        self.current_task = asyncio.create_task(move_with_retry())
        self.state.target_height = height

    async def _async_set_height(self, height: int) -> bool:
        try:
            await self.driver.connect()
            await self.driver.subscribe(callback=self._update_state)
            await self.driver.wake_up()
            await self.driver.stop()
            stationary_count = 0
            while True:
                await self.driver.move_to_height(height)
                await asyncio.sleep(0.1)

                # log current state
                logger.debug(
                    f"Current Height: {self.state.current_height}, "
                    f"Target Height: {self.state.target_height}, "
                    f"Is Moving: {self.state.is_moving}"
                )

                # Success case: Target reached
                if self.state.current_height == height:
                    logger.info(f"Target height {height} reached.")
                    return True

                # Safety/Obstruction case: Desk stopped moving unexpectedly
                if not self.state.is_moving:
                    stationary_count += 1
                    logger.debug(
                        f"Desk stopped moving. Stationary count: {stationary_count}"
                    )
                    # 0.1s sleep * 20 = 2 seconds
                    if stationary_count >= 20:
                        logger.warning(
                            "Desk stopped moving for 2s (Obstruction detected or limit reached)."
                        )
                        return False
                else:
                    stationary_count = 0
        except asyncio.CancelledError:
            logger.info("Movement task was canceled.")
            return False
        except Exception as e:
            logger.error(f"Error setting desk height to {height}: {e}")
            return False
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
