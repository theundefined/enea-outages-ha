"""Tests for the Enea Outages sensors."""

from datetime import datetime
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
                Outage(
                    region="Poznań",
                    description="Planned outage street Testowa 2",
                    start_time=datetime(2025, 12, 2, 8, 0),
                    end_time=datetime(2025, 12, 2, 16, 0),
                ),
                Outage(
                    region="Poznań",
                    description="Planned outage street Inna 1",
                    start_time=datetime(2025, 12, 1, 9, 0),
                    end_time=datetime(2025, 12, 1, 17, 0),
                ),
            ],
            # Unplanned outages
            [
                Outage(
                    region="Poznań",
                    description="Unplanned outage street Testowa 1",
                    start_time=None,
                    end_time=datetime(2025, 12, 1, 14, 0),
                ),
                Outage(
                    region="Poznań",
                    description="Unplanned outage street Inna 1",
                    start_time=None,
                    end_time=datetime(2025, 12, 1, 15, 0),
                ),
            ],
        ]
        yield mock_get_outages


@pytest.mark.asyncio
async def test_sensors_no_street(hass: HomeAssistant, mock_get_outages_for_region) -> None:
    """Test sensors when no street is configured."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_REGION: "Poznań", CONF_STREET: ""},
        entry_id="test-no-street",
        unique_id="Poznań_",
    )
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    # Planned Count Sensor
    planned_count_sensor = hass.states.get("sensor.enea_outages_poznan_planned_outages_count")
    assert planned_count_sensor.state == "3"
    assert "outages" in planned_count_sensor.attributes
    assert len(planned_count_sensor.attributes["outages"]) == 3  # All 3 planned outages

    # Unplanned Count Sensor
    unplanned_count_sensor = hass.states.get("sensor.enea_outages_poznan_unplanned_outages_count")
    assert unplanned_count_sensor.state == "2"
    assert "outages" in unplanned_count_sensor.attributes
    assert len(unplanned_count_sensor.attributes["outages"]) == 2  # All 2 unplanned outages

    # Planned Summary Sensor
    planned_summary_sensor = hass.states.get("sensor.enea_outages_poznan_planned_outages_summary")
    assert planned_summary_sensor.state == "Od: 2025-12-01 08:00 do: 16:00 (Planned outage street Testowa 1)"
    assert "outages" in planned_summary_sensor.attributes
    assert len(planned_summary_sensor.attributes["outages"]) == 3  # All 3 planned outages

    # Unplanned Summary Sensor
    unplanned_summary_sensor = hass.states.get("sensor.enea_outages_poznan_unplanned_outages_summary")
    assert unplanned_summary_sensor.state == "Do: 2025-12-01 14:00 (Unplanned outage street Testowa 1)"
    assert "outages" in unplanned_summary_sensor.attributes
    assert len(unplanned_summary_sensor.attributes["outages"]) == 2  # All 2 unplanned outages


@pytest.mark.asyncio
async def test_sensors_with_street(hass: HomeAssistant, mock_get_outages_for_region) -> None:
    """Test sensors when a street is configured."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_REGION: "Poznań", CONF_STREET: "Testowa"},
        entry_id="test-with-street",
        unique_id="Poznań_Testowa",
    )
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    # Planned Count Sensor
    planned_count_sensor = hass.states.get("sensor.enea_outages_poznan_testowa_planned_outages_count")
    assert planned_count_sensor.state == "2"  # Only Testowa outages
    assert "outages" in planned_count_sensor.attributes
    assert len(planned_count_sensor.attributes["outages"]) == 2

    # Unplanned Count Sensor
    unplanned_count_sensor = hass.states.get("sensor.enea_outages_poznan_testowa_unplanned_outages_count")
    assert unplanned_count_sensor.state == "1"  # Only Testowa outages
    assert "outages" in unplanned_count_sensor.attributes
    assert len(unplanned_count_sensor.attributes["outages"]) == 1

    # Planned Summary Sensor
    planned_summary_sensor = hass.states.get("sensor.enea_outages_poznan_testowa_planned_outages_summary")
    assert planned_summary_sensor.state == "Od: 2025-12-01 08:00 do: 16:00 (Planned outage street Testowa 1)"
    assert "outages" in planned_summary_sensor.attributes
    assert len(planned_summary_sensor.attributes["outages"]) == 2

    # Unplanned Summary Sensor
    unplanned_summary_sensor = hass.states.get("sensor.enea_outages_poznan_testowa_unplanned_outages_summary")
    assert unplanned_summary_sensor.state == "Do: 2025-12-01 14:00 (Unplanned outage street Testowa 1)"
    assert "outages" in unplanned_summary_sensor.attributes
    assert len(unplanned_summary_sensor.attributes["outages"]) == 1


@pytest.mark.asyncio
async def test_sensors_no_outages(hass: HomeAssistant) -> None:
    """Test sensors when no outages are found."""
    # Mocking client to return no outages at all
    with patch("enea_outages.client.EneaOutagesClient.get_outages_for_region", return_value=[]):
        config_entry = MockConfigEntry(
            domain=DOMAIN,
            data={CONF_REGION: "Poznań", CONF_STREET: "NoOutagesStreet"},
            entry_id="test-no-outages",
            unique_id="Poznań_NoOutagesStreet",
        )
        config_entry.add_to_hass(hass)
        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

        # Planned Count Sensor
        planned_count_sensor = hass.states.get("sensor.enea_outages_poznan_nooutagesstreet_planned_outages_count")
        assert planned_count_sensor.state == "0"
        assert "outages" in planned_count_sensor.attributes
        assert len(planned_count_sensor.attributes["outages"]) == 0

        # Unplanned Count Sensor
        unplanned_count_sensor = hass.states.get("sensor.enea_outages_poznan_nooutagesstreet_unplanned_outages_count")
        assert unplanned_count_sensor.state == "0"
        assert "outages" in unplanned_count_sensor.attributes
        assert len(unplanned_count_sensor.attributes["outages"]) == 0

        # Planned Summary Sensor
        planned_summary_sensor = hass.states.get("sensor.enea_outages_poznan_nooutagesstreet_planned_outages_summary")
        assert planned_summary_sensor.state == "Brak"
        assert "outages" in planned_summary_sensor.attributes
        assert len(planned_summary_sensor.attributes["outages"]) == 0

        # Unplanned Summary Sensor
        unplanned_summary_sensor = hass.states.get(
            "sensor.enea_outages_poznan_nooutagesstreet_unplanned_outages_summary"
        )
        assert unplanned_summary_sensor.state == "Brak"
        assert "outages" in unplanned_summary_sensor.attributes
        assert len(unplanned_summary_sensor.attributes["outages"]) == 0
