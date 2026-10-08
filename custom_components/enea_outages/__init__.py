"""The Enea Outages integration."""

from __future__ import annotations

import logging
from datetime import timedelta

from enea_outages.client import EneaOutagesClient
from enea_outages.models import Outage, OutageType
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_AREA,
    CONF_CITY,
    CONF_REGION,
    DEFAULT_PLANNED_SCAN_INTERVAL,
    DEFAULT_UNPLANNED_SCAN_INTERVAL,
    DOMAIN,
    PLATFORMS,
)

_LOGGER = logging.getLogger(__name__)

# Key identifying one query to the Enea site: (region, area id, city). Config entries that differ
# only by street share it, since the street is filtered locally.
LocationKey = tuple[str, str | None, str | None]

# This is a dict of dictionaries of coordinators per location key and outage type to cache the data
# Key: LocationKey
# Value: dict[OutageType, DataUpdateCoordinator]
COORDINATORS: dict[LocationKey, dict[OutageType, DataUpdateCoordinator]] = {}


def location_key(entry: ConfigEntry) -> LocationKey:
    """Return the coordinator key for a config entry."""
    city = entry.data.get(CONF_CITY)
    return (entry.data[CONF_REGION], entry.data.get(CONF_AREA), city.lower() if city else None)


class EneaOutagesOutageTypeCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Enea Outages data for a specific outage type."""

    def __init__(self, hass: HomeAssistant, key: LocationKey, outage_type: OutageType) -> None:
        """Initialize."""
        self.key = key
        self.region, self.area, self.city = key
        self.outage_type = outage_type
        update_interval = (
            DEFAULT_PLANNED_SCAN_INTERVAL if outage_type == OutageType.PLANNED else DEFAULT_UNPLANNED_SCAN_INTERVAL
        )
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{'_'.join(part for part in key if part)}_{outage_type.value}",
            update_interval=timedelta(seconds=update_interval),
        )

    def _fetch_outages(self) -> list[Outage]:
        """Fetch outages, closing the HTTP connection pool afterwards."""
        with EneaOutagesClient() as client:
            return client.get_outages_for_department(self.region, self.outage_type, area=self.area, city=self.city)

    async def _async_update_data(self) -> list[Outage]:
        """Fetch data from Enea API for the specific outage type."""
        try:
            return await self.hass.async_add_executor_job(self._fetch_outages)
        except Exception as err:
            raise UpdateFailed(
                f"Error communicating with Enea API for {self.outage_type.name} in {self.region}: {err}"
            ) from err


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Enea Outages from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    key = location_key(entry)

    if key not in COORDINATORS:
        COORDINATORS[key] = {}

    # Setup Planned Outages Coordinator
    if OutageType.PLANNED not in COORDINATORS[key]:
        planned_coordinator = EneaOutagesOutageTypeCoordinator(hass, key, OutageType.PLANNED)
        await planned_coordinator.async_config_entry_first_refresh()
        COORDINATORS[key][OutageType.PLANNED] = planned_coordinator
    else:
        planned_coordinator = COORDINATORS[key][OutageType.PLANNED]

    # Setup Unplanned Outages Coordinator
    if OutageType.UNPLANNED not in COORDINATORS[key]:
        unplanned_coordinator = EneaOutagesOutageTypeCoordinator(hass, key, OutageType.UNPLANNED)
        await unplanned_coordinator.async_config_entry_first_refresh()
        COORDINATORS[key][OutageType.UNPLANNED] = unplanned_coordinator
    else:
        unplanned_coordinator = COORDINATORS[key][OutageType.UNPLANNED]

    hass.data[DOMAIN][entry.entry_id] = {
        OutageType.PLANNED: planned_coordinator,
        OutageType.UNPLANNED: unplanned_coordinator,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register the service for manual refresh
    async def handle_update_all_coordinators(call):
        for location_coords in COORDINATORS.values():
            for coordinator in location_coords.values():
                await coordinator.async_request_refresh()

    hass.services.async_register(DOMAIN, "update", handle_update_all_coordinators)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        key = location_key(entry)
        hass.data[DOMAIN].pop(entry.entry_id)

        # Check if any other entries are still using this location's planned coordinator
        if not any(entry_coords[OutageType.PLANNED].key == key for entry_coords in hass.data[DOMAIN].values()):
            COORDINATORS[key].pop(OutageType.PLANNED)

        # Check if any other entries are still using this location's unplanned coordinator
        if not any(entry_coords[OutageType.UNPLANNED].key == key for entry_coords in hass.data[DOMAIN].values()):
            COORDINATORS[key].pop(OutageType.UNPLANNED)

        if not COORDINATORS[key]:  # If both planned and unplanned are gone, remove the location key
            COORDINATORS.pop(key)

    # If all config entries are unloaded, unregister the service
    if not hass.data[DOMAIN]:
        hass.services.async_remove(DOMAIN, "update")

    return unload_ok
