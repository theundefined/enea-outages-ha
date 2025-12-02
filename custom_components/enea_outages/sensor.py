"""Platform for sensor integration."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from enea_outages.models import Outage, OutageType
from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    CONF_REGION,
    CONF_STREET,
    ATTR_DESCRIPTION,
    ATTR_START_TIME,
    ATTR_END_TIME,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""

    street = config_entry.data.get(CONF_STREET)

    # Get the dictionary of coordinators for this entry
    entry_coordinators = hass.data[DOMAIN][config_entry.entry_id]
    planned_coordinator = entry_coordinators[OutageType.PLANNED]
    unplanned_coordinator = entry_coordinators[OutageType.UNPLANNED]

    entities = []

    # Planned Outages Count Sensor
    entities.append(
        EneaOutagesCountSensor(
            planned_coordinator,  # Pass the specific coordinator
            config_entry,
            OutageType.PLANNED,
            SensorEntityDescription(
                key=f"{config_entry.entry_id}_planned_outages_count",
                translation_key="planned_outages_count",
                icon="mdi:power-off",
            ),
            street,
        )
    )

    # Unplanned Outages Count Sensor
    entities.append(
        EneaOutagesCountSensor(
            unplanned_coordinator,  # Pass the specific coordinator
            config_entry,
            OutageType.UNPLANNED,
            SensorEntityDescription(
                key=f"{config_entry.entry_id}_unplanned_outages_count",
                translation_key="unplanned_outages_count",
                icon="mdi:power-off",
            ),
            street,
        )
    )

    # Planned Outages Summary Sensor
    entities.append(
        EneaOutagesSummarySensor(
            planned_coordinator,  # Pass the specific coordinator
            config_entry,
            OutageType.PLANNED,
            SensorEntityDescription(
                key=f"{config_entry.entry_id}_planned_outages_summary",
                translation_key="planned_outages_summary",
                icon="mdi:calendar-clock",
            ),
            street,
        )
    )

    # Unplanned Outages Summary Sensor
    entities.append(
        EneaOutagesSummarySensor(
            unplanned_coordinator,  # Pass the specific coordinator
            config_entry,
            OutageType.UNPLANNED,
            SensorEntityDescription(
                key=f"{config_entry.entry_id}_unplanned_outages_summary",
                translation_key="unplanned_outages_summary",
                icon="mdi:alert-outline",
            ),
            street,
        )
    )

    async_add_entities(entities)


class EneaOutagesBaseSensor(CoordinatorEntity, SensorEntity):
    """Base class for Enea Outages sensors."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator_for_outage_type,  # This will now be a single coordinator
        config_entry: ConfigEntry,
        outage_type: OutageType,
        entity_description: SensorEntityDescription,
        street: str | None,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator_for_outage_type)  # Pass the coordinator here
        self.entity_description = entity_description
        self._config_entry = config_entry
        self._outage_type = outage_type
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
    def _outages_data(self) -> list[Outage]:
        """Return the relevant outages data from the coordinator."""
        # The coordinator already fetches data for the specific outage type
        all_outages = self.coordinator.data

        if self._street:
            return [o for o in all_outages if self._street.lower() in o.description.lower()]
        return all_outages

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()


class EneaOutagesCountSensor(EneaOutagesBaseSensor):
    """Sensor to report the count of Enea Outages."""

    @property
    def native_value(self) -> int:
        """Return the number of outages."""
        return len(self._outages_data)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        attrs = {}
        outages_list = []

        # Sort and limit outages to prevent database overload
        outages = self._outages_data
        if self._outage_type == OutageType.PLANNED:
            outages.sort(key=lambda o: o.start_time if o.start_time else datetime.max)
        else:  # Unplanned
            outages.sort(key=lambda o: o.end_time if o.end_time else datetime.max)

        for outage in outages[:10]:
            outages_list.append(
                {
                    ATTR_DESCRIPTION: outage.description,
                    ATTR_START_TIME: outage.start_time.isoformat() if outage.start_time else None,
                    ATTR_END_TIME: outage.end_time.isoformat() if outage.end_time else None,
                }
            )
        attrs["outages"] = outages_list
        return attrs


class EneaOutagesSummarySensor(EneaOutagesBaseSensor):
    """Sensor to report a summary of Enea Outages."""

    @property
    def native_value(self) -> str:
        """Return the summary of the next outage."""
        outages = self._outages_data

        if not outages:
            return "Brak"

        # Sort outages to find the most relevant one for the summary
        if self._outage_type == OutageType.PLANNED:
            outages.sort(key=lambda o: o.start_time if o.start_time else datetime.max)
            next_outage = outages[0]
            start_time_str = next_outage.start_time.strftime("%Y-%m-%d %H:%M") if next_outage.start_time else "Nieznany"
            end_time_str = next_outage.end_time.strftime("%H:%M") if next_outage.end_time else "Nieznany"
            return f"Od: {start_time_str} do: {end_time_str} ({next_outage.description})"
        else:  # Unplanned
            outages.sort(key=lambda o: o.end_time if o.end_time else datetime.max)
            current_outage = outages[0]
            end_time_str = current_outage.end_time.strftime("%Y-%m-%d %H:%M") if current_outage.end_time else "Nieznany"
            return f"Do: {end_time_str} ({current_outage.description})"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        attrs = {}
        outages_list = []

        # Sort and limit outages to prevent database overload
        outages = self._outages_data
        if self._outage_type == OutageType.PLANNED:
            outages.sort(key=lambda o: o.start_time if o.start_time else datetime.max)
        else:  # Unplanned
            outages.sort(key=lambda o: o.end_time if o.end_time else datetime.max)

        for outage in outages[:10]:
            outages_list.append(
                {
                    ATTR_DESCRIPTION: outage.description,
                    ATTR_START_TIME: outage.start_time.isoformat() if outage.start_time else None,
                    ATTR_END_TIME: outage.end_time.isoformat() if outage.end_time else None,
                }
            )
        attrs["outages"] = outages_list
        return attrs
