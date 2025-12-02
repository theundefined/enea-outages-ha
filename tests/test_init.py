"""Test the Enea Outages integration setup."""

from unittest.mock import patch

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.enea_outages.const import DOMAIN, CONF_REGION


@pytest.fixture
def mock_enea_client_get_outages():
    """Fixture to mock EneaOutagesClient.get_outages_for_region."""
    with patch("enea_outages.client.EneaOutagesClient.get_outages_for_region", autospec=True) as mock_get_outages:
        mock_get_outages.return_value = []  # By default, return no outages
        yield mock_get_outages


@pytest.mark.asyncio
async def test_setup_and_unload_entry(hass: HomeAssistant, mock_enea_client_get_outages) -> None:
    """Test successful setup and unload of a config entry."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_REGION: "Poznań", "street": "Testowa"},
        entry_id="test-entry",
        unique_id="Poznań_Testowa",
    )
    config_entry.add_to_hass(hass)

    # Setup the entry
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert config_entry.state == ConfigEntryState.LOADED
    # Assert that the client was called at least twice (for planned and unplanned)
    assert mock_enea_client_get_outages.call_count >= 2

    # Unload the entry
    assert await hass.config_entries.async_unload(config_entry.entry_id)
    await hass.async_block_till_done()

    assert config_entry.state == ConfigEntryState.NOT_LOADED
    assert not hass.data[DOMAIN]  # Ensure all data is cleaned up
