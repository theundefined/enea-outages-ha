"""Config flow for Enea Outages integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from enea_outages.client import EneaOutagesClient
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.selector import (
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .const import CONF_AREA, CONF_AREA_NAME, CONF_CITY, CONF_REGION, CONF_STREET, DEFAULT_REGION, DOMAIN

_LOGGER = logging.getLogger(__name__)


def _fetch_departments() -> list[str]:
    with EneaOutagesClient() as client:
        return client.get_available_departments()


def _fetch_areas(department: str) -> dict[str, str]:
    with EneaOutagesClient() as client:
        return client.get_available_areas(department)


def build_unique_id(region: str, area: str | None, city: str | None, street: str | None) -> str:
    """Build a unique ID for a location; matches the pre-area format when only region/street are set."""
    unique_id = region
    if area:
        unique_id += f"_area-{area}"
    if city:
        unique_id += f"_city-{city.strip().lower().replace(' ', '_')}"
    if street:
        unique_id += f"_{street.replace(' ', '_')}"
    return unique_id


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Enea Outages."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the flow."""
        self._region: str | None = None
        self._areas: dict[str, str] = {}

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle the initial step: choose the Enea Operator branch (oddział)."""
        errors: dict[str, str] = {}
        available_regions = []
        try:
            available_regions = await self.hass.async_add_executor_job(_fetch_departments)
        except Exception as e:
            _LOGGER.error("Failed to get available regions: %s", e)
            errors["base"] = "cannot_connect"

        if user_input is not None:
            region = user_input[CONF_REGION]
            if not errors and region not in available_regions:
                errors["base"] = "invalid_region"

            if not errors:
                self._region = region
                return await self.async_step_location()

        data_schema = vol.Schema(
            {
                vol.Required(CONF_REGION, default=DEFAULT_REGION): vol.In(available_regions),
            }
        )

        return self.async_show_form(step_id="user", data_schema=data_schema, errors=errors)

    async def async_step_location(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle the second step: optionally narrow down to an area (rejon), city and street."""
        errors: dict[str, str] = {}
        region = self._region

        if user_input is None:
            try:
                self._areas = await self.hass.async_add_executor_job(_fetch_areas, region)
            except Exception as e:
                _LOGGER.error("Failed to get areas for %s: %s", region, e)
                self._areas = {}
        else:
            area = user_input.get(CONF_AREA) or None
            city = (user_input.get(CONF_CITY) or "").strip() or None
            street = (user_input.get(CONF_STREET) or "").strip() or None

            if area and area not in self._areas:
                errors[CONF_AREA] = "invalid_area"

            if not errors:
                await self.async_set_unique_id(build_unique_id(region, area, city, street))
                self._abort_if_unique_id_configured()

                data: dict[str, Any] = {CONF_REGION: region}
                if area:
                    data[CONF_AREA] = area
                    data[CONF_AREA_NAME] = self._areas[area]
                if city:
                    data[CONF_CITY] = city
                if street:
                    data[CONF_STREET] = street

                title = ", ".join(part for part in (region, data.get(CONF_AREA_NAME), city, street) if part)
                return self.async_create_entry(title=title, data=data)

        schema: dict[Any, Any] = {}
        if self._areas:
            schema[vol.Optional(CONF_AREA)] = SelectSelector(
                SelectSelectorConfig(
                    options=[SelectOptionDict(value=area_id, label=name) for area_id, name in self._areas.items()],
                    mode=SelectSelectorMode.DROPDOWN,
                )
            )
        schema[vol.Optional(CONF_CITY)] = str
        schema[vol.Optional(CONF_STREET)] = str

        return self.async_show_form(
            step_id="location",
            data_schema=vol.Schema(schema),
            errors=errors,
            description_placeholders={"region": region},
        )
