"""The Enea Outages integration."""

from __future__ import annotations

import logging
from datetime import timedelta

from enea_outages.client import EneaOutagesClient
from functools import partial
from enea_outages.models import Outage, OutageType
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, CONF_REGION, DEFAULT_PLANNED_SCAN_INTERVAL, DEFAULT_UNPLANNED_SCAN_INTERVAL, PLATFORMS


_LOGGER = logging.getLogger(__name__)

# This is a dict of dictionaries of coordinators per region and outage type to cache the data
# Key: region name (str)
# Value: dict[OutageType, DataUpdateCoordinator]
COORDINATORS: dict[str, dict[OutageType, DataUpdateCoordinator]] = {}


class EneaOutagesOutageTypeCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Enea Outages data for a specific outage type."""

    def __init__(self, hass: HomeAssistant, region: str, outage_type: OutageType) -> None:
        """Initialize."""
        self.region = region
        self.outage_type = outage_type
        update_interval = (
            DEFAULT_PLANNED_SCAN_INTERVAL if outage_type == OutageType.PLANNED else DEFAULT_UNPLANNED_SCAN_INTERVAL
        )
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{region}_{outage_type.value}",
            update_interval=timedelta(seconds=update_interval),
        )

    async def _async_update_data(self) -> list[Outage]:
        """Fetch data from Enea API for the specific outage type."""
        try:
            client = EneaOutagesClient()
            return await self.hass.async_add_executor_job(
                partial(client.get_outages_for_region, region=self.region, outage_type=self.outage_type)
            )
        except Exception as err:
            raise UpdateFailed(
                f"Error communicating with Enea API for {self.outage_type.name} in {self.region}: {err}"
            ) from err


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Enea Outages from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    region = entry.data[CONF_REGION]

    if region not in COORDINATORS:
        COORDINATORS[region] = {}

    # Setup Planned Outages Coordinator
    if OutageType.PLANNED not in COORDINATORS[region]:
        planned_coordinator = EneaOutagesOutageTypeCoordinator(hass, region, OutageType.PLANNED)
        await planned_coordinator.async_config_entry_first_refresh()
        COORDINATORS[region][OutageType.PLANNED] = planned_coordinator
    else:
        planned_coordinator = COORDINATORS[region][OutageType.PLANNED]

    # Setup Unplanned Outages Coordinator
    if OutageType.UNPLANNED not in COORDINATORS[region]:
        unplanned_coordinator = EneaOutagesOutageTypeCoordinator(hass, region, OutageType.UNPLANNED)
        await unplanned_coordinator.async_config_entry_first_refresh()
        COORDINATORS[region][OutageType.UNPLANNED] = unplanned_coordinator
    else:
        unplanned_coordinator = COORDINATORS[region][OutageType.UNPLANNED]

    hass.data[DOMAIN][entry.entry_id] = {
        OutageType.PLANNED: planned_coordinator,
        OutageType.UNPLANNED: unplanned_coordinator,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register the service for manual refresh
    async def handle_update_all_coordinators(call):
        for region_coords in COORDINATORS.values():
            for coordinator in region_coords.values():
                await coordinator.async_request_refresh()

    hass.services.async_register(DOMAIN, "update", handle_update_all_coordinators)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        region = entry.data[CONF_REGION]
        hass.data[DOMAIN].pop(entry.entry_id)

        # Check if any other entries are still using this region's planned coordinator
        if not any(entry_coords[OutageType.PLANNED].region == region for entry_coords in hass.data[DOMAIN].values()):
            COORDINATORS[region].pop(OutageType.PLANNED)

        # Check if any other entries are still using this region's unplanned coordinator
        if not any(entry_coords[OutageType.UNPLANNED].region == region for entry_coords in hass.data[DOMAIN].values()):
            COORDINATORS[region].pop(OutageType.UNPLANNED)

        if not COORDINATORS[region]:  # If both planned and unplanned are gone, remove the region key
            COORDINATORS.pop(region)

    # If all config entries are unloaded, unregister the service
    if not hass.data[DOMAIN]:
        hass.services.async_remove(DOMAIN, "update")

    return unload_ok
