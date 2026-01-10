"""This module defines the application's configuration settings."""

import re
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    mac_address: str = "0C6E3937-78B4-BA7E-A934-D4C5C9EDEC2A"
    adapter_name: str = "hci0"
    max_height: int = 1400
    min_height: int = 600

    @field_validator("mac_address")
    @classmethod
    def validate_mac_address(cls, v):
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
