"""Shared entity helpers for the Enea Outages integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity import DeviceInfo

from .const import CONF_AREA_NAME, CONF_CITY, CONF_REGION, CONF_STREET, DOMAIN


def build_device_info(config_entry: ConfigEntry) -> DeviceInfo:
    """Build the DeviceInfo shared by all entities of a configured location."""
    location = " - ".join(
        part
        for part in (
            config_entry.data[CONF_REGION],
            config_entry.data.get(CONF_AREA_NAME),
            config_entry.data.get(CONF_CITY),
            config_entry.data.get(CONF_STREET),
        )
        if part
    )
    device_name = f"Enea Outages ({location})"
    return DeviceInfo(
        identifiers={(DOMAIN, config_entry.entry_id)},
        name=device_name,
        model="Enea Outages Monitor",
        manufacturer="Enea Operator",
    )
