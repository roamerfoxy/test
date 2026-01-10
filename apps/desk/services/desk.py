"""This module provides the business logic for controlling the desk."""

import asyncio
from apps.desk.core.config import settings
from apps.desk.drivers.desk_driver import DeskDriver
from apps.desk.core.state import desk_state, presets
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

    def _update_state(self, height: int, speed: int):
        desk_state.current_height = height
        desk_state.is_moving = speed != 0

    def get_height(self) -> int:
        """Returns the current height of the desk."""
        return desk_state.current_height

    def set_height(self, height: int):
        """Sets the target height of the desk and starts moving asynchronously."""
        logger.info(f"Setting desk height to {height}mm")
        asyncio.create_task(self._async_set_height(height))
        desk_state.target_height = height

    async def _async_set_height(self, height: int):
        try:
            await self.driver.connect()
            await self.driver.subscribe(callback=self._update_state)
            await self.driver.wake_up()
            await self.driver.stop()
            while True:
                await self.driver.move_to_height(height)
                await asyncio.sleep(0.1)
                # print(desk_state.current_height, height)
                if desk_state.current_height == height:
                    break
        except Exception as e:
            logger.error(f"Error setting desk height to {height}: {e}")
            raise
        finally:
            await self.driver.unsubscribe()
            await self.driver.stop()
            await self.driver.disconnect()

    def set_preset(self, preset_name: str):
        """Moves the desk to a preset height."""
        if preset_name in presets.root:
            height = presets.root[preset_name].height
            logger.info(f"Applying preset '{preset_name}' with height {height}mm")
            self.set_height(height)
            desk_state.active_preset = preset_name
        else:
            logger.warning(f"Preset '{preset_name}' not found")
