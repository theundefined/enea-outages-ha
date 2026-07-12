# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A Home Assistant custom integration (`custom_components/enea_outages`) that surfaces planned/unplanned power
outage data from Enea Operator (a Polish energy distributor) as HA sensors and a binary sensor. All actual
scraping/parsing of the Enea website lives in the separate `enea-outages` PyPI package (dependency pinned in
`manifest.json` and `pyproject.toml`); this repo only wires that client into Home Assistant's config-entry /
coordinator model. Do not reimplement scraping logic here — if outage data looks wrong, the bug is likely in the
`enea-outages` library, not this integration.

## Commands

Install (editable, with test/lint extras):
```bash
pip install -e .[test]
```

Run tests (must scope to `tests/` — see gotcha below):
```bash
python -m pytest tests/
```

Run a single test file / test:
```bash
python -m pytest tests/test_sensor.py
python -m pytest tests/test_sensor.py::test_planned_outage_count_sensor -q
```

Lint / format (both run in CI and must pass):
```bash
ruff check .
black --check .      # use `black .` to auto-fix
```

Bump version, tag, and push a release (updates `manifest.json`, commits, tags, pushes to `origin main` and
tags — triggers the `release.yml` workflow which zips the component and creates a GitHub release):
```bash
./release.sh patch   # or: minor | major
```

**Gotcha:** a bare `python -m pytest` (no path) from the repo root will fail with import mismatch errors if a
local `tmp/walutomat-ha-reference/` checkout exists — it's a gitignored reference clone of a sibling HA
integration, not part of this project. Always run pytest against `tests/` explicitly.

## Architecture

**Coordinator sharing across config entries.** `__init__.py` keeps a module-level `COORDINATORS` dict keyed by
`region -> {OutageType.PLANNED | OutageType.UNPLANNED: DataUpdateCoordinator}`, separate from `hass.data[DOMAIN]`
(which is keyed by `entry_id`). This means multiple config entries for the *same region* (e.g. same region, two
different streets) share the same two underlying coordinators/API polls instead of each entry polling
independently — street filtering happens client-side in the entity layer, not in the coordinator. When touching
setup/unload logic, preserve this: `async_unload_entry` must only tear down a region's coordinator once no
remaining config entry references it.

**Two independent poll cadences.** Planned and unplanned outages are fetched by two separate
`DataUpdateCoordinator` instances per region, with different `update_interval`s
(`DEFAULT_PLANNED_SCAN_INTERVAL` = 1h, `DEFAULT_UNPLANNED_SCAN_INTERVAL` = 10min, in `const.py`). Each
coordinator's `_async_update_data` calls `client.get_outages_for_region` (a *sync* call) via
`hass.async_add_executor_job` — the `enea-outages` client is not async, so don't call it directly on the event
loop.

**Entities read directly from `coordinator.data`, filtered by street at render time.** Sensors/binary sensor
don't store their own outage lists; `EneaOutagesBaseSensor._outages_data` (sensor.py) and
`EneaOutagesActiveBinarySensor._filter_outages` (binary_sensor.py) both re-filter the *shared* coordinator's
current `list[Outage]` by substring-matching `street.lower()` against `outage.description.lower()` on every
access. There's no dedicated street/address field on `Outage` — street matching is always a description
substring check.

**The binary sensor listens to both coordinators.** `EneaOutagesActiveBinarySensor` is constructed against the
*planned* coordinator (for the base `CoordinatorEntity` subscription) but also manually subscribes to the
*unplanned* coordinator's updates in `async_added_to_hass` via `async_on_remove(unplanned_coordinator.
add_listener(...))`, since a `CoordinatorEntity` can only natively track one coordinator. It's "on" if any
planned outage's `[start_time, end_time]` window contains `now`, or any unplanned outage's `end_time` is still
in the future (unplanned outages have no known `start_time`).

**Manual refresh service.** `enea_outages.update` (registered in `async_setup_entry`, defined as a no-op schema
in `services.yaml`) walks *all* coordinators for *all* regions, not just the calling entry's — it's a global
force-refresh.

**Config flow** (`config_flow.py`) fetches the live region list from the Enea website
(`client.get_available_regions()`) to populate the region dropdown, and derives the config entry's unique ID
from `region` + optional `street` (spaces replaced with underscores) so the same region/street pair can't be
added twice while different streets in the same region can coexist.

## Testing conventions

Tests use `pytest-homeassistant-custom-component` with `asyncio_mode = auto`. Network access is blocked by the
autouse `socket_enabled`/`auto_mock_socket` fixtures in `tests/conftest.py`; mock `enea_outages.client.
EneaOutagesClient.get_outages_for_region` (see the `mock_get_outages_for_region` fixture pattern in
`test_sensor.py`) rather than hitting the real Enea site. A `--internet-off` pytest flag exists in
`conftest.py` to invert which tests run based on a `@pytest.mark.internet_off` marker, for environments
without network access — no current test uses that marker.
