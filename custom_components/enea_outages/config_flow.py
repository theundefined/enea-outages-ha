"""Config flow for Enea Outages integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from enea_outages.client import EneaOutagesClient
from .const import DOMAIN, CONF_REGION, CONF_STREET, DEFAULT_REGION

_LOGGER = logging.getLogger(__name__)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Enea Outages."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        available_regions = []
        try:
            client = EneaOutagesClient()
            available_regions = await self.hass.async_add_executor_job(client.get_available_regions)
        except Exception as e:
            _LOGGER.error("Failed to get available regions: %s", e)
            errors["base"] = "cannot_connect"

        if user_input is not None:
            region = user_input[CONF_REGION]
            street = user_input.get(CONF_STREET)

            # Generate a unique ID for the config entry based on region and street
            unique_id = f"{region}"
            if street:
                unique_id += f"_{street.replace(' ', '_')}"
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()

            if not errors and region not in available_regions:
                errors["base"] = "invalid_region"

            if not errors:
                title = region
                if street:
                    title += f", {street}"
                return self.async_create_entry(title=title, data=user_input)

        data_schema = vol.Schema(
            {
                vol.Required(CONF_REGION, default=DEFAULT_REGION): vol.In(available_regions),
                vol.Optional(CONF_STREET): str,
            }
        )

        return self.async_show_form(step_id="user", data_schema=data_schema, errors=errors)
