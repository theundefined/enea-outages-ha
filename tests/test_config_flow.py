"""Test the Enea Outages config flow."""

from unittest.mock import MagicMock, patch

import pytest
from homeassistant import config_entries, data_entry_flow
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.enea_outages.const import CONF_AREA, CONF_AREA_NAME, CONF_CITY, CONF_REGION, CONF_STREET, DOMAIN

AREAS = {"7": "Poznań", "10": "Szamotuły"}


@pytest.fixture
def mock_client() -> MagicMock:
    """Mock the Enea client used by the config flow."""
    with patch("custom_components.enea_outages.config_flow.EneaOutagesClient") as mock_client_class:
        client = mock_client_class.return_value
        client.__enter__.return_value = client
        client.get_available_departments.return_value = ["Poznań", "Szczecin"]
        client.get_available_areas.side_effect = lambda department: AREAS if department == "Poznań" else {}
        yield client


@pytest.fixture(autouse=True)
def mock_setup_entry():
    """Avoid setting up the integration when an entry is created."""
    with patch("custom_components.enea_outages.async_setup_entry", return_value=True):
        yield


async def _start_location_step(hass: HomeAssistant, region: str) -> dict:
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "user"
    assert not result["errors"]

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {CONF_REGION: region})
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "location"
    return result


@pytest.mark.asyncio
async def test_form_whole_region(hass: HomeAssistant, mock_client: MagicMock) -> None:
    """Test configuring an entry for a whole region."""
    result = await _start_location_step(hass, "Poznań")
    assert CONF_AREA in result["data_schema"].schema

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {CONF_CITY: "", CONF_STREET: ""})
    await hass.async_block_till_done()

    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result["title"] == "Poznań"
    assert result["data"] == {CONF_REGION: "Poznań"}
    assert result["result"].unique_id == "Poznań"


@pytest.mark.asyncio
async def test_form_with_street(hass: HomeAssistant, mock_client: MagicMock) -> None:
    """Test configuring an entry with a street keeps the pre-area unique ID format."""
    result = await _start_location_step(hass, "Szczecin")
    # Szczecin has no areas, so the area field is not shown.
    assert CONF_AREA not in result["data_schema"].schema

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {CONF_STREET: "Wojska Polskiego"})
    await hass.async_block_till_done()

    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result["title"] == "Szczecin, Wojska Polskiego"
    assert result["data"] == {CONF_REGION: "Szczecin", CONF_STREET: "Wojska Polskiego"}
    assert result["result"].unique_id == "Szczecin_Wojska_Polskiego"


@pytest.mark.asyncio
async def test_form_with_area_city_and_street(hass: HomeAssistant, mock_client: MagicMock) -> None:
    """Test configuring an entry narrowed down to an area, city and street."""
    result = await _start_location_step(hass, "Poznań")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_AREA: "10", CONF_CITY: " Obrzycko ", CONF_STREET: "Rynek"}
    )
    await hass.async_block_till_done()

    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result["title"] == "Poznań, Szamotuły, Obrzycko, Rynek"
    assert result["data"] == {
        CONF_REGION: "Poznań",
        CONF_AREA: "10",
        CONF_AREA_NAME: "Szamotuły",
        CONF_CITY: "Obrzycko",
        CONF_STREET: "Rynek",
    }
    assert result["result"].unique_id == "Poznań_area-10_city-obrzycko_Rynek"
    mock_client.get_available_areas.assert_called_once_with("Poznań")


@pytest.mark.asyncio
async def test_form_areas_unavailable(hass: HomeAssistant, mock_client: MagicMock) -> None:
    """Test the location step still works when areas cannot be fetched."""
    mock_client.get_available_areas.side_effect = Exception("Connection error")

    result = await _start_location_step(hass, "Poznań")
    assert CONF_AREA not in result["data_schema"].schema

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {CONF_CITY: "Poznań"})
    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result["data"] == {CONF_REGION: "Poznań", CONF_CITY: "Poznań"}


@pytest.mark.asyncio
async def test_form_cannot_connect(hass: HomeAssistant, mock_client: MagicMock) -> None:
    """Test we handle cannot connect error during region fetching."""
    mock_client.get_available_departments.side_effect = Exception("Connection error")

    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}


@pytest.mark.asyncio
async def test_form_invalid_region(hass: HomeAssistant, mock_client: MagicMock) -> None:
    """Test we handle an invalid region selection."""
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    assert result["type"] == data_entry_flow.FlowResultType.FORM

    with pytest.raises(data_entry_flow.InvalidData):
        await hass.config_entries.flow.async_configure(result["flow_id"], {CONF_REGION: "Invalid Region"})


@pytest.mark.asyncio
async def test_form_already_configured(hass: HomeAssistant, mock_client: MagicMock) -> None:
    """Test we abort if a location configured before areas existed is added again."""
    MockConfigEntry(
        domain=DOMAIN,
        data={CONF_REGION: "Poznań", CONF_STREET: "Testowa"},
        unique_id="Poznań_Testowa",
    ).add_to_hass(hass)

    result = await _start_location_step(hass, "Poznań")
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {CONF_STREET: "Testowa"})

    assert result["type"] == data_entry_flow.FlowResultType.ABORT
    assert result["reason"] == "already_configured"
