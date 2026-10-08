"""Test the Enea Outages integration setup."""

from unittest.mock import patch

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.enea_outages.const import CONF_AREA, CONF_AREA_NAME, CONF_CITY, CONF_REGION, DOMAIN


@pytest.fixture
def mock_enea_client_get_outages():
    """Fixture to mock EneaOutagesClient.get_outages_for_department."""
    with patch("enea_outages.client.EneaOutagesClient.get_outages_for_department", autospec=True) as mock_get_outages:
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


@pytest.mark.asyncio
async def test_setup_entry_with_area_and_city(hass: HomeAssistant, mock_enea_client_get_outages) -> None:
    """Test that area and city are passed to the Enea client and kept separate from other locations."""
    from enea_outages.models import OutageType

    from custom_components.enea_outages import COORDINATORS

    narrowed_entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_REGION: "Poznań", CONF_AREA: "10", CONF_AREA_NAME: "Szamotuły", CONF_CITY: "Obrzycko"},
        entry_id="narrowed-entry",
        unique_id="Poznań_area-10_city-obrzycko",
    )
    whole_region_entry = MockConfigEntry(
        domain=DOMAIN, data={CONF_REGION: "Poznań"}, entry_id="region-entry", unique_id="Poznań"
    )
    narrowed_entry.add_to_hass(hass)
    whole_region_entry.add_to_hass(hass)

    # Setting up the integration loads every config entry of the domain.
    await hass.config_entries.async_setup(narrowed_entry.entry_id)
    await hass.async_block_till_done()
    assert whole_region_entry.state == ConfigEntryState.LOADED

    calls = {
        (c.args[2], c.kwargs.get("area"), c.kwargs.get("city")) for c in mock_enea_client_get_outages.call_args_list
    }
    assert (OutageType.PLANNED, "10", "obrzycko") in calls
    assert (OutageType.UNPLANNED, "10", "obrzycko") in calls
    assert (OutageType.PLANNED, None, None) in calls
    assert set(COORDINATORS) == {("Poznań", "10", "obrzycko"), ("Poznań", None, None)}

    devices = dr.async_entries_for_config_entry(dr.async_get(hass), "narrowed-entry")
    assert [device.name for device in devices] == ["Enea Outages (Poznań - Szamotuły - Obrzycko)"]

    assert await hass.config_entries.async_unload(narrowed_entry.entry_id)
    assert await hass.config_entries.async_unload(whole_region_entry.entry_id)
    await hass.async_block_till_done()
    assert not COORDINATORS
