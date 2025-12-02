"""Global fixtures for Enea Outages integration tests."""

import pytest
from unittest.mock import patch

# This fixture enables loading custom components from the custom_components folder
pytest_plugins = "pytest_homeassistant_custom_component"


def pytest_addoption(parser):
    """Add options to pytest."""
    parser.addoption("--internet-off", action="store_true", default=False)


# This fixture is used to prevent HomeAssistant from attempting to create and dismiss persistent
# notifications. These calls would fail without this fixture since the persistent_notification
# integration is not loaded during tests.
@pytest.fixture(autouse=True)
def prevent_persistent_notification(hass):
    """Prevent persistent notification calls during tests."""
    with patch("homeassistant.components.persistent_notification.async_create"), patch(
        "homeassistant.components.persistent_notification.async_dismiss"
    ):
        yield


# This fixture, when used, will result in skipping all tests that require the internet.
@pytest.fixture(autouse=True)
def skip_on_internet_errors(request):
    """Skip tests that require internet."""
    if request.node.get_closest_marker("internet_off"):
        if not request.config.getoption("--internet-off"):
            pytest.skip("skipping internet-off tests")
        return
    if request.config.getoption("--internet-off"):
        pytest.skip("skipping internet tests")


# This fixture autouses TCP socket mocking to prevent real network requests.
@pytest.fixture(autouse=True)
def auto_mock_socket(socket_enabled):
    """Enable socket mocking for all tests."""
    pass


# This fixture enables custom integrations and mocks the zeroconf component.
@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(hass, enable_custom_integrations, mock_zeroconf):
    """Enable custom integrations and mock zeroconf."""
    yield
