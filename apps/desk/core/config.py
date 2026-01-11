"""This module defines the application's configuration settings."""

import re
import platform
from typing import Optional
from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    # Explicit override for all platforms
    mac_address: Optional[str] = None

    # OS-specific defaults
    macos_mac_address: str = "0C6E3937-78B4-BA7E-A934-D4C5C9EDEC2A"
    linux_mac_address: str = "FD:46:77:A9:30:CA"

    adapter_name: str = "hci0"
    max_height: int = 1400
    min_height: int = 600
    presets_file: str = "data/presets.json"

    @model_validator(mode="after")
    def set_default_mac_address(self) -> "Settings":
        if self.mac_address is None:
            if platform.system() == "Darwin":
                self.mac_address = self.macos_mac_address
            else:
                self.mac_address = self.linux_mac_address
        return self

    @field_validator("mac_address", "macos_mac_address", "linux_mac_address")
    @classmethod
    def validate_mac_address(cls, v):
        if v is None:
            return v
        # Allow both colon-separated and UUID-like formats
        if not (
            re.match(r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$", v)
            or re.match(
                r"^[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}$",
                v,
            )
        ):
            raise ValueError(
                "MAC address must be in format XX:XX:XX:XX:XX:XX or UUID format"
            )
        return v.upper()

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="DESK_",
    )


settings = Settings()
