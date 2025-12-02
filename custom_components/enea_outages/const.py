"""Constants for the Enea Outages integration."""

DOMAIN = "enea_outages"
PLATFORMS = ["sensor", "binary_sensor"]

CONF_REGION = "region"
CONF_STREET = "street"

DEFAULT_REGION = "Poznań"
DEFAULT_PLANNED_SCAN_INTERVAL = 3600  # 1 hour
DEFAULT_UNPLANNED_SCAN_INTERVAL = 600  # 10 minutes

ATTR_OUTAGE_TYPE = "outage_type"
ATTR_DESCRIPTION = "description"
ATTR_START_TIME = "start_time"
ATTR_END_TIME = "end_time"
