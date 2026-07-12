"""Shared entity helpers for the Enea Outages integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN


def build_device_info(config_entry: ConfigEntry, region: str, street: str | None) -> DeviceInfo:
    """Build the DeviceInfo shared by all entities of a configured location."""
    device_name = f"Enea Outages ({region}{' - ' + street if street else ''})"
    return DeviceInfo(
        identifiers={(DOMAIN, config_entry.entry_id)},
        name=device_name,
        model="Enea Outages Monitor",
        manufacturer="Enea Operator",
    )
