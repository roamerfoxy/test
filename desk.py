"""
This module provides a Desk class for controlling an IKEA desk via Bluetooth Low Energy (BLE).
It includes functionality for moving the desk to predefined positions and monitoring its height.
"""

from __future__ import annotations
from typing import Optional, Callable, Any
from enum import Enum
from dataclasses import dataclass
import functools
import asyncio
import os
import struct
import json
from bleak import BleakClient, BleakScanner
from bleak.backends.device import BLEDevice
from bleak.exc import BleakError
from apps.desk.core import logger

logger_desk = logger.get_logger(__name__)

BASE_HEIGHT = 620
MAX_HEIGHT = 1270

UUID_HEIGHT = "99fa0021-338a-1024-8a49-009c0215f78a"
UUID_COMMAND = "99fa0002-338a-1024-8a49-009c0215f78a"
UUID_REFERENCE_INPUT = "99fa0031-338a-1024-8a49-009c0215f78a"

COMMAND_UP = bytearray(struct.pack("<H", 71))
COMMAND_DOWN = bytearray(struct.pack("<H", 70))
COMMAND_STOP = bytearray(struct.pack("<H", 255))
COMMAND_WAKEUP = bytearray(struct.pack("<H", 254))

COMMAND_REFERENCE_INPUT_STOP = bytearray(struct.pack("<H", 32769))
COMMAND_REFERENCE_INPUT_UP = bytearray(struct.pack("<H", 32768))
COMMAND_REFERENCE_INPUT_DOWN = bytearray(struct.pack("<H", 32767))

DEFAULT_CONFIG_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CONFIG_FILE = "desk_config.json"

DEFAULT_DESK_CONFIG = {
    "mac_address": "FD:46:77:A9:30:CA",
    "adapter_name": "hci0",
    "position_3": BASE_HEIGHT + 530,
    "position_2": BASE_HEIGHT + 430,
    "position_1": BASE_HEIGHT + 80,
    "height_tolerance": 1,
    "scan_timeout": 5,
    "connection_attempt": 5,
    "movement_attempt": 5,
}


@dataclass
class DeskConfig:
    """
    Configuration class for the Desk.

    Attributes:
        mac_address (str): The MAC address of the desk's BLE device.
        adapter_name (str): The name of the Bluetooth adapter to use.
        position_3 (int): The height in mm for position 3.
        position_2 (int): The height in mm for position 2.
        position_1 (int): The height in mm for position 1.
        height_tolerance (int): The acceptable tolerance for height adjustments.
        scan_timeout (int): The timeout in seconds for BLE device scanning.
        connection_attempt (int): The number of BLE connection attempts.
        movement_attempt (int): The number of desk movement operations.
    """

    mac_address: str
    adapter_name: str
    position_3: int
    position_2: int
    position_1: int
    height_tolerance: int
    scan_timeout: int
    connection_attempt: int
    movement_attempt: int


class DeskPosition(Enum):
    """
    Enumeration of available desk positions.
    """

    SIT = "position_1"
    STAND = "position_2"
    READ = "position_3"


def mm_to_raw(mm: int) -> int:
    """
    Convert a desk height in millimeters to a raw desk height value.

    Args:
        mm (int): The height in millimeters.

    Returns:
        int: The raw desk height value.
    """
    return (mm - BASE_HEIGHT) * 10


def raw_to_mm(raw: int) -> int:
    """
    Convert a raw desk height value to millimeters.

    Args:
        raw (int): The raw desk height value.

    Returns:
        int: The height in millimeters.
    """
    return (raw // 10) + BASE_HEIGHT


class Desk:
    """
    A class to control and monitor an IKEA desk via Bluetooth Low Energy.
    """

    def __init__(self):
        """Initialize the Desk object with default configuration and state."""
        self.config: DeskConfig = self.load_config()
        self.device: Optional[BLEDevice] = None
        self.client: Optional[BleakClient] = None
        self.disconnecting: bool = False
        self.desk_height: int = 0
        self.desk_speed: int = 0

    def load_config(self, config_file: str = DEFAULT_CONFIG_FILE) -> DeskConfig:
        """
        Load the desk configuration from a JSON file.

        Args:
            config_file (str): The path to the configuration file.

        Returns:
            DeskConfig: The loaded configuration.
        """
        try:
            config_file = os.path.join(DEFAULT_CONFIG_DIR, config_file)
            logger_desk.info("Loading config file: %s", config_file)
            with open(config_file, "r", encoding="utf-8") as f:
                config_data = json.load(f)
            return DeskConfig(
                **{k: config_data.get(k, v) for k, v in DEFAULT_DESK_CONFIG.items()}
            )
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger_desk.exception("Error loading config: %s", e)
            return DeskConfig(**DEFAULT_DESK_CONFIG)

    async def scan(self, mac_address: str = DEFAULT_DESK_CONFIG["mac_address"]) -> None:
        """
        Scan for the desk's BLE device.

        Args:
            mac_address (str): The MAC address of the desk's BLE device.

        Raises:
            BleakError: If the device is not found.
        """
        logger_desk.info("Scanning: mac_addr %s", mac_address)
        device = await BleakScanner.find_device_by_address(
            mac_address, timeout=self.config.scan_timeout
        )
        if device is None:
            logger_desk.error("Could not find device with address %s", mac_address)
            raise BleakError(f"Device with address {mac_address} not found")
        logger_desk.info("Device found: %s", device.details)
        self.device = device

    def disconnect_callback(self, _: Any) -> None:
        """Callback function to handle BLE disconnections."""
        if self.client:
            logger_desk.info("Disconnected from %s", self.client.address)
        if not self.disconnecting:
            logger_desk.info("Reconnecting...")
            asyncio.create_task(self.connect(self.config.connection_attempt))

    async def connect(
        self, attempt: int = DEFAULT_DESK_CONFIG["connection_attempt"]
    ) -> None:
        """
        Connect to the desk's BLE device.

        Args:
            attempt (int): The number of connection attempts to make.

        Raises:
            BleakError: If connection fails after all attempts.
        """
        if self.device:
            try:
                self.client = BleakClient(
                    self.device, disconnected_callback=self.disconnect_callback
                )
                logger_desk.info(
                    "Connecting to %s with %d times remained",
                    self.device.name,
                    attempt - 1,
                )
                await self.client.connect()
                logger_desk.info("Desk %s connected", self.client.address)
            except (BleakError, asyncio.TimeoutError) as err:
                if attempt > 0:
                    logger_desk.warning(
                        "Connection failure. Attempts remaining: %d. Error: %s",
                        attempt - 1,
                        err,
                    )
                    await asyncio.sleep(1)
                    await self.connect(attempt=attempt - 1)
                else:
                    logger_desk.exception(
                        "Connection failed after all attempts. Error: %s", err
                    )
                    raise

    async def disconnect(self) -> None:
        """Disconnect from the desk's BLE device."""
        if self.client and self.client.is_connected:
            self.disconnecting = True
            await self.client.disconnect()
            logger_desk.info("Desk %s disconnected", self.client.address)

    def get_height_data_from_notification(
        self, _: Any, data: bytearray, *, callback: Callable[[str], None]
    ) -> None:
        """
        Process height data received from BLE notifications.

        Args:
            _ (Any): Unused parameter.
            data (bytearray): The raw data received from the BLE device.
            callback (Callable[[str], None]): A callback function to handle the processed data.
        """
        height, speed = struct.unpack("<Hh", data)
        self.desk_height = int(raw_to_mm(height))
        self.desk_speed = speed
        logger_desk.debug(
            "Current height: %d, speed: %d from notification in desk object",
            self.desk_height,
            self.desk_speed,
        )
        callback(f"Height: {self.desk_height}; Speed: {self.desk_speed}")

    async def subscribe(
        self, callback: Callable[[Any, bytearray], None], uuid: str = UUID_HEIGHT
    ) -> None:
        """
        Subscribe to BLE notifications for a specific characteristic.

        Args:
            callback (Callable[[Any, bytearray], None]): The callback function to handle notifications.
            uuid (str): The UUID of the characteristic to subscribe to.
        """
        if self.client and self.client.is_connected:
            await self.client.start_notify(uuid, callback)
            logger_desk.info(
                "Callback %s subscribed to client %s",
                callback,
                self.client,
            )

    async def unsubscribe(self, uuid: str) -> None:
        """
        Unsubscribe from BLE notifications for a specific characteristic.

        Args:
            uuid (str): The UUID of the characteristic to unsubscribe from.
        """
        if self.client and self.client.is_connected:
            await self.client.stop_notify(uuid)
            logger_desk.info("Unsubscribed from %s", uuid)

    async def wake_up(self) -> None:
        """Send a wake-up command to the desk."""
        if self.client and self.client.is_connected:
            await self.client.write_gatt_char(UUID_COMMAND, COMMAND_WAKEUP)

    async def stop_move(self) -> None:
        """Send a stop movement command to the desk."""
        if self.client and self.client.is_connected:
            await self.client.write_gatt_char(UUID_COMMAND, COMMAND_STOP)
            await self.client.write_gatt_char(
                UUID_REFERENCE_INPUT, COMMAND_REFERENCE_INPUT_STOP
            )

    async def move_to(self, target: int) -> None:
        """
        Send a command to move the desk to a specific height.

        Args:
            target (int): The target height in millimeters.
        """
        if self.client and self.client.is_connected:
            encoded_target = bytearray(struct.pack("<H", int(mm_to_raw(target))))
            await self.client.write_gatt_char(UUID_REFERENCE_INPUT, encoded_target)

    async def move_desk_to_target(self, target: int) -> bool:
        """
        Move the desk to a target height and wait for completion.

        Args:
            target (int): The target height in millimeters.

        Returns:
            bool: True if the movement was successful, False otherwise.
        """
        await self.wake_up()
        await self.stop_move()

        while True:
            await self.move_to(target)
            await asyncio.sleep(0.4)

            if self.desk_speed == 0:
                logger_desk.info("Desk speed is 0, stop moving")
                break

        logger_desk.info(
            "Current height: %d, target height: %d", self.desk_height, target
        )

        return int(self.desk_height) == target

    async def move_desk_to_position(
        self, position: DeskPosition, call_back_func: Callable[[str], None]
    ) -> bool:
        """
        Move the desk to a predefined position.

        Args:
            position (DeskPosition): The target position enum.
            call_back_func (Callable[[str], None]): A callback function to handle status updates.

        Returns:
            bool: True if the movement was successful, False otherwise.
        """
        if self.device is None:
            logger_desk.error("Desk device is not found, scan desk first")
            return False

        try:
            async with self:
                await self.subscribe(
                    functools.partial(
                        self.get_height_data_from_notification, callback=call_back_func
                    ),
                )

                success = False
                for attempt in range(self.config.movement_attempt):
                    success = await self.move_desk_to_target(
                        getattr(self.config, position.value)
                    )
                    logger_desk.info("Success: %s, Attempt: %d", success, attempt + 1)
                    if success:
                        break
                    await asyncio.sleep(1)
                return success
        except BleakError as err:
            logger_desk.exception("Error in move_desk_to_position: %s", err)
            return False

    async def __aenter__(self) -> Desk:
        """Async context manager entry point."""
        await self.connect(self.config.connection_attempt)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit point."""
        await self.stop_move()
        await self.disconnect()


def log_msg(msg: str) -> None:
    """
    Simple logging function to print messages.

    Args:
        msg (str): The message to log.
    """
    print(msg)


async def main() -> None:
    """
    Main function to demonstrate the usage of the Desk class.
    """
    try:
        ikea_desk = Desk()
        await ikea_desk.scan(ikea_desk.config.mac_address)

        # await ikea_desk.move_desk_to_position(DeskPosition.STAND, log_msg)
        # await asyncio.sleep(1)
        await ikea_desk.move_desk_to_position(DeskPosition.SIT, log_msg)
    except (BleakError, asyncio.TimeoutError) as err:
        logger_desk.exception("Error in main: %s", err)


if __name__ == "__main__":
    asyncio.run(main())
