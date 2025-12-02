"""Tests for the Enea Outages binary sensor."""

from datetime import datetime, timedelta
from unittest.mock import patch

import pytest
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.enea_outages.const import DOMAIN, CONF_REGION, CONF_STREET
from enea_outages.models import Outage


@pytest.fixture
def mock_get_outages_for_region():
    """Fixture to mock EneaOutagesClient.get_outages_for_region."""
    with patch("enea_outages.client.EneaOutagesClient.get_outages_for_region", autospec=True) as mock_get_outages:
        # Default return values for planned and unplanned
        mock_get_outages.side_effect = [
            # Planned outages
            [
                Outage(
                    region="Poznań",
                    description="Planned outage street Testowa 1",
                    start_time=datetime(2025, 12, 1, 8, 0),
                    end_time=datetime(2025, 12, 1, 16, 0),
                ),
                Outage(  # Active planned outage
                    region="Poznań",
                    description="Planned outage street Testowa 2 (active)",
                    start_time=datetime.now().replace(microsecond=0) - timedelta(hours=1),
                    end_time=datetime.now().replace(microsecond=0) + timedelta(hours=1),
                ),
            ],
            # Unplanned outages
            [
                Outage(
                    region="Poznań",
                    description="Unplanned outage street Testowa 1",
                    start_time=None,
                    end_time=datetime.now().replace(microsecond=0) + timedelta(minutes=30),  # Active unplanned outage
                ),
            ],
        ]
        yield mock_get_outages


@pytest.mark.asyncio
async def test_binary_sensor_active(hass: HomeAssistant, mock_get_outages_for_region) -> None:
    """Test the binary sensor is active when outages are present."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_REGION: "Poznań", CONF_STREET: "Testowa"},
        entry_id="test-binary-active",
        unique_id="Poznań_Testowa",
    )
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    binary_sensor = hass.states.get("binary_sensor.enea_outages_poznan_testowa_outage_active")
    assert binary_sensor.state == "on"


@pytest.mark.asyncio
async def test_binary_sensor_inactive(hass: HomeAssistant) -> None:
    """Test the binary sensor is inactive when no outages are present."""
    # Mocking client to return no outages at all
    with patch("enea_outages.client.EneaOutagesClient.get_outages_for_region", return_value=[]):
        config_entry = MockConfigEntry(
            domain=DOMAIN,
            data={CONF_REGION: "Poznań", CONF_STREET: "NoOutagesStreet"},
            entry_id="test-binary-inactive",
            unique_id="Poznań_NoOutagesStreet",
        )
        config_entry.add_to_hass(hass)
        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

        binary_sensor = hass.states.get("binary_sensor.enea_outages_poznan_nooutagesstreet_outage_active")
        assert binary_sensor.state == "off"
