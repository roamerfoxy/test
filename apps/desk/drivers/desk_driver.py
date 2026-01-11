"""This module implements the driver for controlling the desk via BLE."""

import asyncio
import struct
from typing import Optional, Any, Callable

from bleak import BleakClient, BleakScanner
from bleak.backends.device import BLEDevice
from bleak.exc import BleakError

from apps.desk.core.logger import get_logger

logger = get_logger(__name__)

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

BASE_HEIGHT = 620


def raw_to_mm(raw: int) -> int:
    """Converts a raw height value from the desk to millimeters."""
    return (raw // 10) + BASE_HEIGHT


def mm_to_raw(mm: int) -> int:
    """Converts a height in millimeters to the raw value expected by the desk."""
    return (mm - BASE_HEIGHT) * 10


class DeskDriver:
    """
    A driver for controlling a standing desk via Bluetooth Low Energy (BLE).

    This class provides methods to connect to the desk, control its movement,
    and subscribe to height updates.  It uses the Bleak library for BLE communication.

    Attributes:
        mac_address (str): The Bluetooth MAC address of the desk.
        device (Optional[BLEDevice]): The BLEDevice object representing the desk,
            discovered during scanning.  Initialized to None.
        client (Optional[BleakClient]): The BleakClient object for interacting with
            the desk's BLE service. Initialized to None.

    Methods:
        scan(): Discovers the desk using its MAC address.
        connect(): Connects to the desk's BLE service.
        disconnect(): Disconnects from the desk's BLE service.
        wake_up(): Sends a wake-up command to the desk.
        stop(): Sends a stop command to the desk.
        move_to_height(target_mm: int): Moves the desk to the specified height in millimeters.
        subscribe(callback: Callable[[int, int], None]): Subscribes to height and speed updates from the desk. The callback function is called with the height and speed values.
        unsubscribe(): Unsubscribes from height and speed updates.
    """

    def __init__(self, mac_address: str):
        """Initializes the DeskDriver with the desk's MAC address."""
        self.mac_address = mac_address
        self.device: Optional[BLEDevice] = None
        self.client: Optional[BleakClient] = None

    async def scan(self):
        """
        Scans for the desk device using its MAC address.

        Raises:
            BleakError: If the device is not found.
        """
        self.device = await BleakScanner.find_device_by_address(self.mac_address)
        if not self.device:
            raise BleakError(f"Device {self.mac_address} not found")

    async def connect(self):
        """
        Connects to the desk's BLE service.

        Raises:
            BleakError: If the device is not found or connection fails.
        """
        if not self.device:
            await self.scan()
        if self.device is None:
            raise BleakError("Device not found, cannot connect")
        self.client = BleakClient(self.device)
        await asyncio.wait_for(self.client.connect(), timeout=10.0)
        logger.info("Connected to desk")

    async def disconnect(self):
        """Disconnects from the desk's BLE service if connected."""
        try:
            if self.client and self.client.is_connected:
                await self.client.disconnect()
        except (BleakError, EOFError, Exception) as e:
            logger.warning(
                f"Error during disconnect (possibly already disconnected): {e}"
            )
        finally:
            self.client = None

    async def wake_up(self):
        """Sends a wake-up command to the desk."""
        if self.client and self.client.is_connected:
            await self.client.write_gatt_char(UUID_COMMAND, COMMAND_WAKEUP)

    async def stop(self):
        """Sends a stop command to the desk."""
        if self.client and self.client.is_connected:
            await self.client.write_gatt_char(UUID_COMMAND, COMMAND_STOP)
            await self.client.write_gatt_char(
                UUID_REFERENCE_INPUT, COMMAND_REFERENCE_INPUT_STOP
            )

    async def move_to_height(self, target_mm: int):
        """
        Moves the desk to the specified height in millimeters.

        Args:
            target_mm (int): The target height in millimeters.
        """
        if self.client and self.client.is_connected:
            encoded_target = bytearray(struct.pack("<H", int(mm_to_raw(target_mm))))
            await self.client.write_gatt_char(UUID_REFERENCE_INPUT, encoded_target)

    async def subscribe(self, callback: Callable[[int, int], None]):
        """
        Subscribes to height and speed updates from the desk.

        The callback function is called with the height and speed values.

        Args:
            callback (Callable[[int, int], None]): A function to be called with the
                height (mm) and speed (unitless) when the desk reports a change.
        """

        def _state_callback(_: Any, data: bytearray):
            height_raw, speed = struct.unpack("<HH", data)
            height = raw_to_mm(height_raw)
            callback(height, speed)

        if self.client and self.client.is_connected:
            await self.client.start_notify(UUID_HEIGHT, _state_callback)

    async def unsubscribe(self):
        """Unsubscribes from height and speed updates."""
        if self.client and self.client.is_connected:
            await self.client.stop_notify(UUID_HEIGHT)
