"""Platform for binary_sensor integration."""

from __future__ import annotations

import logging
from datetime import datetime

from enea_outages.models import Outage, OutageType
from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, CONF_REGION, CONF_STREET

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the binary_sensor platform."""

    street = config_entry.data.get(CONF_STREET)

    # Get the dictionary of coordinators for this entry
    entry_coordinators = hass.data[DOMAIN][config_entry.entry_id]
    planned_coordinator = entry_coordinators[OutageType.PLANNED]
    unplanned_coordinator = entry_coordinators[OutageType.UNPLANNED]

    entities = []

    # Combined Outage Active Binary Sensor
    entities.append(
        EneaOutagesActiveBinarySensor(
            planned_coordinator,  # Base on planned coordinator for updates
            unplanned_coordinator,  # Use unplanned coordinator for data
            config_entry,
            BinarySensorEntityDescription(
                key=f"{config_entry.entry_id}_outage_active",
                translation_key="outage_active",
                icon="mdi:power-plug-off",
            ),
            street,
        )
    )

    async_add_entities(entities)


class EneaOutagesActiveBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Binary sensor to indicate if any outage is currently active."""

    _attr_has_entity_name = True

    def __init__(
        self,
        planned_coordinator,
        unplanned_coordinator,
        config_entry: ConfigEntry,
        entity_description: BinarySensorEntityDescription,
        street: str | None,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(planned_coordinator)  # Subscribe to planned coordinator for updates
        self._unplanned_coordinator = unplanned_coordinator  # Keep a reference to the unplanned coordinator
        self.entity_description = entity_description
        self._config_entry = config_entry
        self._street = street
        self._region = config_entry.data[CONF_REGION]

        self._attr_unique_id = f"{config_entry.entry_id}_{entity_description.key}"

        device_name = f"Enea Outages ({self._region}{' - ' + self._street if self._street else ''})"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, config_entry.entry_id)},
            name=device_name,
            model="Enea Outages Monitor",
            manufacturer="Enea Operator",
        )

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        now = datetime.now()

        # Check planned outages
        planned_outages = self._filter_outages(self.coordinator.data)
        for outage in planned_outages:
            if outage.start_time and outage.end_time and outage.start_time <= now <= outage.end_time:
                return True

        # Check unplanned outages
        unplanned_outages = self._filter_outages(self._unplanned_coordinator.data)
        for outage in unplanned_outages:
            # Unplanned outages typically only have an end_time. Assume they are active if end_time is in the future.
            if outage.end_time and now <= outage.end_time:
                return True

        return False

    def _filter_outages(self, all_outages: list[Outage]) -> list[Outage]:
        """Filter outages by street if provided."""
        if self._street:
            return [o for o in all_outages if self._street.lower() in o.description.lower()]
        return all_outages

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the planned coordinator."""
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        # Also listen to the unplanned coordinator updates
        self.async_on_remove(self._unplanned_coordinator.async_add_listener(self._handle_coordinator_update))
